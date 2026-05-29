"""Unit tests for ``packaging/velopack/convert_icon.py``.

The converter takes SVG bytes and emits multi-size Windows ICO bytes. The
tests use a small synthetic SVG fixture so no external assets are required
and no real filesystem writes occur during the conversion.

Import note:
    The script lives under ``packaging/velopack/`` which is NOT a Python
    package on import. ``packaging`` is the name of a third-party PyPI
    package that pytest itself imports, so adding ``__init__.py`` files
    under the repo's ``packaging/`` directory would shadow that package
    and break the test runner. The tests therefore load the converter
    via :func:`importlib.util.spec_from_file_location` from its source
    path, which keeps the conversion behavior testable without
    interfering with pytest's own dependencies.
"""

from __future__ import annotations

import importlib.util
import io
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from PIL import Image

if TYPE_CHECKING:
    from types import ModuleType


def _load_convert_icon() -> ModuleType:
    """Load the converter module from its source path.

    Purpose:
        Resolve the path to ``packaging/velopack/convert_icon.py`` and
        load it via the importlib machinery so the conversion code is
        callable without registering a top-level ``packaging`` package.
        The loaded module is cached in :data:`sys.modules` under an
        alias so repeated calls return the same instance.

    Returns:
        The loaded :class:`ModuleType` representing the converter.

    Raises:
        ImportError: When the source file cannot be located or loaded.
    """
    cached = sys.modules.get("_test_convert_icon_module")
    if cached is not None:
        return cached
    source = (
        Path(__file__).resolve().parents[1]
        / "packaging"
        / "velopack"
        / "convert_icon.py"
    )
    spec = importlib.util.spec_from_file_location("_test_convert_icon_module", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load converter from {source!s}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["_test_convert_icon_module"] = module
    spec.loader.exec_module(module)
    return module


# Synthetic SVG fixture: a single filled red rectangle at 256x256. Small
# enough to keep the test fast yet exercises every code path in the real
# converter (parse, rasterize, convert to PIL, assemble multi-size ICO).
_SYNTHETIC_SVG: bytes = (
    b'<?xml version="1.0" encoding="UTF-8"?>\n'
    b'<svg xmlns="http://www.w3.org/2000/svg" '
    b'viewBox="0 0 256 256">'
    b'<rect width="256" height="256" fill="#ff0000"/>'
    b"</svg>"
)


def test_convert_icon_main_writes_multisize_ico() -> None:
    """AC5/AC6: convert_svg_bytes_to_ico_bytes produces a valid multi-size ICO.

    Verifies the magic-byte header, the four expected frame sizes
    (16, 32, 48, 256), and round-trips the output through Pillow without
    touching the filesystem.
    """
    # Arrange / Act: rasterize the synthetic SVG into ICO bytes.
    convert_icon = _load_convert_icon()
    ico_bytes = convert_icon.convert_svg_bytes_to_ico_bytes(_SYNTHETIC_SVG)

    # Assert (header): the first four bytes are the Windows ICO magic.
    assert ico_bytes[:4] == b"\x00\x00\x01\x00"

    # Assert (frames): re-open the ICO via Pillow and read the embedded
    # frame sizes. The set of (width, height) pairs must equal the
    # documented size tuple.
    image = Image.open(io.BytesIO(ico_bytes))
    # Pillow exposes the ICO frame sizes through Image.info["sizes"] (a
    # set of (w, h) tuples). The comparison is order-independent.
    sizes = image.info.get("sizes")
    assert sizes is not None
    expected = {(s, s) for s in convert_icon.ICON_SIZES}
    assert set(sizes) == expected


def test_convert_icon_main_exits_zero_with_path_args(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC6: main returns 0 and writes ICO bytes via the injected seam.

    The test patches the read and write seams so no filesystem I/O occurs.
    The recorder captures the bytes that would have been written and
    verifies the magic header propagated through the seam.
    """
    convert_icon = _load_convert_icon()
    recorded: dict[str, bytes | Path] = {}

    def fake_read(path: Path) -> bytes:
        # Record which path the script claimed it read.
        recorded["read_path"] = path
        return _SYNTHETIC_SVG

    def fake_write(path: Path, data: bytes) -> None:
        # Record the output path and the bytes the script would have written.
        recorded["write_path"] = path
        recorded["write_data"] = data

    monkeypatch.setattr(convert_icon, "read_svg_bytes", fake_read)
    monkeypatch.setattr(convert_icon, "write_ico_bytes", fake_write)

    rc = convert_icon.main(["--input", "x.svg", "--output", "y.ico"])

    assert rc == 0
    # The script forwarded the resolved paths to the seams unchanged.
    assert recorded["read_path"] == Path("x.svg")
    assert recorded["write_path"] == Path("y.ico")
    # The bytes written carry the ICO magic header.
    data = recorded["write_data"]
    assert isinstance(data, bytes)
    assert data[:4] == b"\x00\x00\x01\x00"


def test_convert_icon_rejects_missing_qsvgrenderer_load() -> None:
    """convert_svg_bytes_to_ico_bytes raises ValueError on invalid SVG bytes.

    A garbage payload that QSvgRenderer cannot parse must surface as a
    clear ValueError so a corrupted source SVG is reported at the
    boundary instead of silently producing a blank ICO.
    """
    convert_icon = _load_convert_icon()
    with pytest.raises(ValueError, match=r"(?i)svg|parse"):
        convert_icon.convert_svg_bytes_to_ico_bytes(b"not svg")
