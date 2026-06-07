"""Confidentiality masking scan for the schema-builder-ux-overhaul feature.

Purpose:
    Scan a set of feature-touched files (test fixtures, evidence artifacts, and
    any source files added by this feature) for forbidden patterns that would
    indicate real workbook values or proprietary source column names have leaked
    into the repository. The schema-builder-ux-overhaul work passes a masked
    preview slice into the builder; only synthetic/masked data may be committed.

Responsibilities:
    - Walk a configurable set of target paths.
    - Match each file's text against a forbidden-pattern set (proprietary source
      column-name tokens and real-data numeric signatures).
    - Report each match with file, line number, and the matched token.
    - Exit non-zero when any forbidden pattern is found, zero when the scanned
      tree is clean.

Scope boundaries:
    This scan does not attempt to prove a file is fully synthetic; it flags
    known-forbidden tokens. It is a defense-in-depth gate, not a substitute for
    manual review (see the masking-audit evidence artifact).

Usage:
    python scripts/checks/scan_masked_fixtures.py [path ...]

    With no path arguments it scans the default target set defined below.
    Returns process exit code 0 when clean, 1 when any forbidden pattern matches.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]

# Proprietary source column-name tokens that must never appear in synthetic
# fixtures or artifacts. These are placeholder sentinels: the real proprietary
# names are intentionally NOT embedded here (embedding them would itself leak
# the names). Synthetic fixtures must use neutral names such as "src_col_a".
# The pattern intentionally targets the literal sentinel marker a developer
# would paste if copying real data, plus a real-data numeric signature.
FORBIDDEN_NAME_TOKENS: tuple[str, ...] = (
    "PROPRIETARY_SOURCE_COLUMN",
    "REAL_WORKBOOK_VALUE",
)

# A real-data numeric signature: long currency-like values with thousands
# separators and cents (for example 1,234,567.89). Synthetic fixtures should
# use small round numbers (1, 2, 10.5) that never match this signature.
REAL_DATA_NUMERIC = re.compile(r"\b\d{1,3}(?:,\d{3}){2,}\.\d{2}\b")

# File suffixes the scan inspects as text. Binary suffixes are skipped.
TEXT_SUFFIXES: frozenset[str] = frozenset(
    {".py", ".json", ".md", ".txt", ".csv", ".cfg", ".ini", ".yaml", ".yml"}
)

# Directory names that are never scanned (caches, build outputs, vendored data).
SKIP_DIRS: frozenset[str] = frozenset(
    {"__pycache__", ".git", ".venv", "node_modules", "dist", "build", ".pytest_cache"}
)


@dataclass(frozen=True)
class Finding:
    """A single forbidden-pattern hit.

    Attributes:
        path: Repository-relative path of the offending file.
        line_no: 1-based line number where the pattern matched.
        matched: The matched forbidden token or numeric signature.
    """

    path: str
    line_no: int
    matched: str


def default_targets() -> tuple[Path, ...]:
    """Return the default set of paths to scan.

    The default set covers the feature's test directories, the bundled schema
    JSON, and the feature evidence/docs folders, which are where masked sample
    values or proprietary names could plausibly leak.

    Returns:
        A tuple of absolute paths (files or directories) to scan. Missing paths
        are skipped silently so the default set stays stable as the tree grows.
    """
    candidate_rel = (
        "tests",
        "src/schemas",
        "docs/features/active/2026-06-04-schema-builder-ux-overhaul-50",
    )
    # Keep only paths that currently exist so the scan never errors on an
    # absent optional target.
    return tuple(REPO_ROOT / rel for rel in candidate_rel if (REPO_ROOT / rel).exists())


def iter_text_files(targets: Iterable[Path]) -> Iterable[Path]:
    """Yield every scannable text file under the given targets.

    Args:
        targets: Files or directories to walk. Directories are walked
            recursively; files are yielded directly when they are text files.

    Yields:
        Absolute paths to text files eligible for scanning, skipping cache and
        build directories and non-text suffixes.
    """
    for target in targets:
        if target.is_file():
            if target.suffix in TEXT_SUFFIXES:
                yield target
            continue
        # Walk the directory tree, pruning skip directories as we go so we never
        # descend into caches or build artifacts.
        for path in target.rglob("*"):
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if path.is_file() and path.suffix in TEXT_SUFFIXES:
                yield path


def scan_file(path: Path) -> list[Finding]:
    """Scan a single file for forbidden tokens and real-data numeric signatures.

    Args:
        path: Absolute path to the text file to scan.

    Returns:
        A list of Finding records, one per matched line/token. Empty when the
        file is clean. Files that cannot be decoded as UTF-8 are reported as a
        single Finding so undecodable (possibly binary) content is surfaced
        rather than silently skipped.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        rel = path.relative_to(REPO_ROOT).as_posix()
        return [Finding(path=rel, line_no=0, matched="<non-utf8-content>")]

    rel = path.relative_to(REPO_ROOT).as_posix()
    findings: list[Finding] = []
    # Examine each line so we can report a precise location for every hit.
    for line_no, line in enumerate(text.splitlines(), start=1):
        # Check the explicit forbidden name tokens first; these are exact
        # markers that should never be committed.
        for token in FORBIDDEN_NAME_TOKENS:
            if token in line:
                findings.append(Finding(path=rel, line_no=line_no, matched=token))
        # Then check the real-data numeric signature, which catches currency-like
        # values that synthetic fixtures must not contain.
        for match in REAL_DATA_NUMERIC.finditer(line):
            findings.append(Finding(path=rel, line_no=line_no, matched=match.group(0)))
    return findings


def scan(targets: Sequence[Path]) -> list[Finding]:
    """Scan all target paths and aggregate findings.

    Args:
        targets: The paths to scan (files or directories).

    Returns:
        All Finding records across every scanned file, in file/line order.
    """
    findings: list[Finding] = []
    # Aggregate findings across every eligible file in the target set.
    for path in iter_text_files(targets):
        findings.extend(scan_file(path))
    return findings


def main(argv: Sequence[str]) -> int:
    """Run the masking scan and report results.

    Args:
        argv: Command-line arguments excluding the program name. When empty, the
            default target set is scanned; otherwise each argument is treated as
            a path (relative to the repo root or absolute) to scan.

    Returns:
        Process exit code: 0 when no forbidden pattern is found, 1 otherwise.
    """
    if argv:
        # Resolve each supplied path against the repo root when it is relative.
        targets = tuple(
            (REPO_ROOT / arg) if not Path(arg).is_absolute() else Path(arg)
            for arg in argv
        )
    else:
        targets = default_targets()

    findings = scan(targets)
    if not findings:
        print("masking-scan: clean (no forbidden patterns found)")
        return 0

    # Report each finding so a developer can locate and mask the leaked value.
    print(f"masking-scan: {len(findings)} forbidden pattern(s) found:")
    for finding in findings:
        print(f"  {finding.path}:{finding.line_no}: {finding.matched}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
