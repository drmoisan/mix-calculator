"""One-shot SVG-to-multi-size-ICO converter for the Velopack installer.

Purpose:
    Convert the committed source SVG at
    ``packaging/velopack/icon-source.svg`` into the multi-size Windows
    ICO consumed by ``vpk pack --icon`` and embedded in the Nuitka
    standalone executable via ``--windows-icon-from-ico``. The script
    rasterizes the SVG at 16, 32, 48, and 256 pixels using
    :class:`PySide6.QtSvg.QSvgRenderer` and assembles the multi-frame
    ICO via Pillow's ``Image.save(..., format='ICO', sizes=[...])``.

Responsibilities:
    * Parse a CLI argv of the form ``--input <svg-path> --output
      <ico-path>``.
    * Read the SVG bytes via the :func:`read_svg_bytes` seam.
    * Rasterize each size using :class:`QSvgRenderer` into an in-memory
      :class:`QImage`, convert it to a :class:`PIL.Image.Image`, and
      assemble the multi-frame ICO into an :class:`io.BytesIO` buffer.
    * Write the ICO bytes via the :func:`write_ico_bytes` seam.

Usage:
    ``poetry run python packaging/velopack/convert_icon.py
    --input packaging/velopack/icon-source.svg
    --output packaging/velopack/icon.ico``

    Tests substitute :func:`read_svg_bytes` and :func:`write_ico_bytes`
    so the conversion runs entirely in memory without temp files.

Side Effects:
    On the production path the script reads the source SVG from disk
    and writes the produced ICO to disk. Both I/O operations flow
    through injected seams so unit tests can drive the conversion
    without filesystem dependencies.

Dependencies:
    * PySide6 (runtime dep) supplies ``QtSvg.QSvgRenderer`` plus the
      ``QApplication`` host required by the Qt image pipeline.
    * Pillow (dev-only build-time dep declared in ``pyproject.toml``
      under ``[tool.poetry.group.dev.dependencies]``) supplies
      multi-frame ICO assembly via ``Image.save(..., format='ICO',
      sizes=[...])``.
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Final

from PIL import Image
from PySide6.QtCore import QByteArray, QCoreApplication, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication

if TYPE_CHECKING:
    from collections.abc import Sequence

# Fixed ICO frame sizes (Windows convention): 16/32/48 are required for
# Explorer thumbnails and the system tray; 256 is the high-DPI variant
# embedded as PNG-compressed inside the ICO container.
ICON_SIZES: Final[tuple[int, ...]] = (16, 32, 48, 256)


def _ensure_qapplication() -> None:
    """Ensure a singleton :class:`QCoreApplication` instance exists.

    Purpose:
        ``QSvgRenderer`` and ``QPainter`` require a Qt application
        instance to manage the image pipeline. The helper constructs a
        :class:`QApplication` only when none exists so repeated calls
        in the same process do not double-construct.

    Returns:
        ``None``.

    Side Effects:
        On first call, constructs a :class:`QApplication` with empty
        argv. Subsequent calls are no-ops.
    """
    if QCoreApplication.instance() is None:
        # Construct the Qt application with empty argv; the converter
        # never reads ``sys.argv`` directly, and the application only
        # needs to exist as a parent for the image pipeline.
        QApplication([])


def _render_svg_to_qimage(svg_bytes: bytes, size: int) -> QImage:
    """Rasterize ``svg_bytes`` into a square :class:`QImage` of ``size`` px.

    Purpose:
        Drive :class:`QSvgRenderer` to render the SVG into a
        ``QImage`` of the requested resolution. The result uses the
        ARGB32 pixel format so alpha-channel transparency survives the
        conversion to PIL.

    Args:
        svg_bytes: The raw SVG payload.
        size: The square edge length in pixels (matches ICO_SIZES).

    Returns:
        A square :class:`QImage` of the requested size containing the
        rasterized SVG. The painter is finalized before return.

    Raises:
        ValueError: When :class:`QSvgRenderer` reports the payload is
            unparseable. The message includes the requested size so the
            failing rasterization step is identifiable.

    Side Effects:
        Initializes a :class:`QApplication` on first invocation (via
        :func:`_ensure_qapplication`).
    """
    _ensure_qapplication()
    # QSvgRenderer.load accepts QByteArray; the renderer's isValid()
    # check is the boundary at which a malformed SVG surfaces. We must
    # call it before painting because the painter would otherwise
    # silently produce a transparent image.
    renderer = QSvgRenderer(QByteArray(svg_bytes))
    if not renderer.isValid():
        raise ValueError(
            f"SVG could not be parsed at size {size}; the QSvgRenderer "
            f"reported isValid() == False."
        )

    # Allocate the destination QImage with explicit ARGB32 format so
    # alpha-channel transparency is preserved through the paint step.
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)

    # Painter lifecycle: construct, render, finalize. The end() call
    # before return is essential — leaving the painter active would
    # leave the destination image's backing buffer in an undefined
    # state for subsequent reads.
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    return image


def _qimage_to_pil(image: QImage) -> Image.Image:
    """Convert a :class:`QImage` to a Pillow :class:`Image.Image`.

    Purpose:
        Bridge Qt's ``QImage`` (used by ``QSvgRenderer``) to Pillow's
        ``Image.Image`` (used by the ICO assembler) via direct pixel-
        buffer access. The source is normalized to RGBA8888 so the
        resulting bytes have a deterministic channel order and the
        alpha channel survives the conversion.

    Args:
        image: The source ``QImage`` from :func:`_render_svg_to_qimage`.

    Returns:
        An RGBA-mode Pillow ``Image`` of the same dimensions.

    Side Effects:
        Allocates a transient byte buffer when ``bytesPerLine`` differs
        from ``width * 4`` (the row-stride correction path).
    """
    # Normalize the pixel layout so the channel order is unambiguous:
    # RGBA8888 lays bytes out as R, G, B, A, which is identical to
    # Pillow's ``"RGBA"`` mode and avoids per-platform byte-order
    # surprises on the ARGB32 native layout.
    rgba = image.convertToFormat(QImage.Format.Format_RGBA8888)
    width = rgba.width()
    height = rgba.height()
    bytes_per_line = rgba.bytesPerLine()
    expected_stride = width * 4

    # Direct buffer view: constBits() returns a memoryview over the
    # QImage's backing buffer. The view is only valid as long as the
    # QImage is alive, so we materialize the bytes immediately.
    raw = bytes(rgba.constBits())

    # Stride correction: when bytesPerLine includes per-row padding,
    # walk each scanline and slice the row payload so PIL receives a
    # tight (width * 4)-stride RGBA buffer.
    if bytes_per_line != expected_stride:
        # Concatenate trimmed scanlines into a tight RGBA buffer.
        trimmed = bytearray(expected_stride * height)
        for row in range(height):
            start = row * bytes_per_line
            trimmed[row * expected_stride : (row + 1) * expected_stride] = raw[
                start : start + expected_stride
            ]
        raw = bytes(trimmed)

    return Image.frombytes("RGBA", (width, height), raw)


def convert_svg_bytes_to_ico_bytes(svg_bytes: bytes) -> bytes:
    """Convert SVG bytes into multi-size ICO bytes.

    Purpose:
        Rasterize the SVG at each size in :data:`ICON_SIZES`, convert
        each ``QImage`` to a Pillow ``Image.Image``, and assemble the
        multi-frame ICO via Pillow's ``Image.save(..., format='ICO',
        sizes=[...])``. The output buffer is returned as raw bytes so
        the caller can write the bytes through the
        :func:`write_ico_bytes` seam.

    Args:
        svg_bytes: The raw SVG payload to convert.

    Returns:
        The ICO container bytes, beginning with the Windows ICO magic
        ``b"\\x00\\x00\\x01\\x00"`` and containing one frame per size
        in :data:`ICON_SIZES`.

    Raises:
        ValueError: When the SVG cannot be parsed at any rasterization
            size (propagated from :func:`_render_svg_to_qimage`).

    Side Effects:
        Initializes a :class:`QApplication` on first invocation via
        :func:`_ensure_qapplication` and allocates transient PNG
        buffers during the QImage-to-PIL conversion step.
    """
    _ensure_qapplication()

    # Render each requested size into a Pillow image. The comprehension
    # is acceptable here because each step is independent and the
    # intent is single-purpose: produce one PIL image per ICO frame.
    # The largest size becomes the base image passed to Image.save; the
    # remaining sizes are declared via the ``sizes=`` keyword so Pillow
    # writes one ICO frame per requested resolution.
    pil_images: list[Image.Image] = []
    for size in ICON_SIZES:
        qimage = _render_svg_to_qimage(svg_bytes, size)
        pil_images.append(_qimage_to_pil(qimage))

    # The base image is the largest frame; Pillow downscales / packs
    # additional frames according to the ``sizes`` keyword.
    base_image = max(pil_images, key=lambda im: im.size[0])
    buffer = io.BytesIO()
    base_image.save(
        buffer,
        format="ICO",
        sizes=[(s, s) for s in ICON_SIZES],
    )
    return buffer.getvalue()


def read_svg_bytes(path: Path) -> bytes:
    """Read raw bytes from ``path``.

    Purpose:
        I/O seam: production code reads the source SVG from disk;
        tests substitute a recorder so no filesystem access occurs.

    Args:
        path: The filesystem path to read.

    Returns:
        The file's raw bytes.

    Side Effects:
        Reads from disk on the production path.
    """
    return path.read_bytes()


def write_ico_bytes(path: Path, data: bytes) -> None:
    """Write ``data`` to ``path`` as a binary file.

    Purpose:
        I/O seam: production code writes the produced ICO to disk;
        tests substitute a recorder so no filesystem access occurs.

    Args:
        path: The destination filesystem path.
        data: The ICO container bytes.

    Returns:
        ``None``.

    Side Effects:
        Writes ``data`` to ``path`` on the production path,
        overwriting any existing file.
    """
    path.write_bytes(data)


def _build_argument_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser for ``--input`` and ``--output``.

    Returns:
        A configured :class:`argparse.ArgumentParser` exposing two
        required value flags: ``--input`` for the source SVG and
        ``--output`` for the destination ICO.

    Side Effects:
        ``None``.
    """
    parser = argparse.ArgumentParser(
        prog="convert_icon",
        description=(
            "Convert a source SVG into a multi-size Windows ICO at "
            "16, 32, 48, and 256 pixels."
        ),
    )
    parser.add_argument(
        "--input",
        dest="input_path",
        type=str,
        required=True,
        help="Path to the source SVG file.",
    )
    parser.add_argument(
        "--output",
        dest="output_path",
        type=str,
        required=True,
        help="Path where the produced ICO will be written.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the one-shot conversion script.

    Purpose:
        Parse CLI args, read the source SVG via :func:`read_svg_bytes`,
        run the conversion, and write the produced ICO bytes via
        :func:`write_ico_bytes`. Both I/O steps flow through injected
        seams so unit tests can run the full conversion in memory.

    Args:
        argv: Optional argv vector. When ``None``, ``argparse`` reads
            ``sys.argv[1:]`` as usual.

    Returns:
        ``0`` on a successful conversion. Non-zero is reserved for
        future error branches; the current implementation lets
        unexpected exceptions propagate so the underlying cause is
        visible in the build log.

    Side Effects:
        Reads from disk (via :func:`read_svg_bytes`) and writes to
        disk (via :func:`write_ico_bytes`). Tests substitute both
        seams so neither call touches the filesystem.
    """
    parser = _build_argument_parser()
    args = parser.parse_args(argv)
    input_path = Path(args.input_path)
    output_path = Path(args.output_path)

    svg_bytes = read_svg_bytes(input_path)
    ico_bytes = convert_svg_bytes_to_ico_bytes(svg_bytes)
    write_ico_bytes(output_path, ico_bytes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
