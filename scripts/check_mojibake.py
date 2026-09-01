"""Reject characteristic text-encoding corruption in repository files.

The default scan uses Git's tracked-file list so scratch files do not create
noise. Explicit file arguments support focused checks and isolated tests. Binary
files are skipped; tracked text that is not valid UTF-8 is reported as a failure.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable


# Escapes keep this source from containing the very corruption it detects.
MOJIBAKE_MARKERS = (
    # UTF-8 em dash decoded through an incompatible code page.
    "\u00d4\u00c7\u00f6",
    "\u00d4\u00eb\u00ea",  # characteristic comparison-symbol corruption
    "\u00e2\u20ac\u201d",  # em dash
    "\u00e2\u20ac\u201c",  # en dash
    "\u00e2\u20ac\u02dc",  # left single quotation mark
    "\u00e2\u20ac\u2122",  # right single quotation mark
    "\u00e2\u20ac\u0153",  # left double quotation mark
    "\u00e2\u20ac\u009d",  # right double quotation mark
    "\u00c2\u0020",  # non-breaking space decoded as a visible prefix plus space
    "\ufffd",  # Unicode replacement character
)

SKIPPED_DIRECTORY_NAMES = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "node_modules",
    }
)


def _repository_root() -> Path:
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return Path(completed.stdout.strip()).resolve()


def _tracked_files(root: Path) -> tuple[Path, ...]:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    names = completed.stdout.decode("utf-8").split("\0")
    return tuple(root / name for name in names if name)


def _is_skipped(path: Path) -> bool:
    return any(part in SKIPPED_DIRECTORY_NAMES for part in path.parts)


def _display_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _scannable_lines(path: Path, text: str) -> Iterable[tuple[int, str]]:
    """Yield prose lines, excluding intentional Markdown code examples."""

    in_fence = False
    for line_number, line in enumerate(text.splitlines(), start=1):
        if path.suffix.casefold() == ".md":
            stripped = line.lstrip()
            if stripped.startswith(("```", "~~~")):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            line = re.sub(r"`[^`]*`", "", line)
        yield line_number, line


def find_violations(
    paths: Iterable[Path], root: Path
) -> tuple[tuple[str, int, str], ...]:
    """Return deterministic ``(path, line, marker)`` mojibake violations."""

    violations: list[tuple[str, int, str]] = []
    for path in sorted((item.resolve() for item in paths), key=lambda item: str(item)):
        if _is_skipped(path) or not path.is_file():
            continue
        content = path.read_bytes()
        if b"\0" in content:
            continue
        display_path = _display_path(path, root)
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as error:
            line_number = content[: error.start].count(b"\n") + 1
            violations.append((display_path, line_number, "<invalid UTF-8>"))
            continue
        for line_number, line in _scannable_lines(path, text):
            for marker in MOJIBAKE_MARKERS:
                if marker in line:
                    violations.append((display_path, line_number, marker))
    return tuple(violations)


def _escaped(marker: str) -> str:
    if marker.startswith("<"):
        return marker
    return marker.encode("unicode_escape").decode("ascii")


def main(arguments: list[str] | None = None) -> int:
    """Scan explicit files or, by default, all Git-tracked repository files."""

    arguments = sys.argv[1:] if arguments is None else arguments
    try:
        root = _repository_root()
        paths = (
            tuple(Path(argument).resolve() for argument in arguments)
            if arguments
            else _tracked_files(root)
        )
        violations = find_violations(paths, root)
    except (OSError, subprocess.CalledProcessError, UnicodeError) as error:
        print(f"mojibake check failed to run: {error}", file=sys.stderr)
        return 2

    for path, line_number, marker in violations:
        print(f"{path}:{line_number}: prohibited mojibake marker {_escaped(marker)}")
    if violations:
        print(f"Found {len(violations)} mojibake violation(s).")
        return 1
    print("Mojibake check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
