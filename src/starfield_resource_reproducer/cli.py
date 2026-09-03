"""Stable command-line boundary for the validated production product.

Purpose: resolve runtime paths and options, invoke the single oracle-free
production service, and present concise status or errors. Domain generation,
product construction, and serialization remain in their dedicated modules.
Diagnostic and oracle-validation modes are deliberately outside this interface.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import os
from pathlib import Path
import sys
import tempfile
import time

from starfield_resource_reproducer import __version__
from starfield_resource_reproducer.product import (
    OUTPUT_FILENAME,
    prepare_product,
    write_prepared_product,
)


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_DATA_DIR = _PROJECT_ROOT / "data"
_INPUT_DEFAULTS = {
    "resource_generation_path": _DEFAULT_DATA_DIR / "planet-resource-generation.csv",
    "resource_tree_path": _DEFAULT_DATA_DIR / "ires-hierarchy.csv",
    "atmospheric_resources_path": _DEFAULT_DATA_DIR / "planet-atmospheric-resources.csv",
    "planet_directory_path": _DEFAULT_DATA_DIR / "planet-directory.csv",
}


class OutputPathUsageError(ValueError):
    """An explicit output value has an invalid command-line form."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="starfield-resource-reproducer",
        description=(
            "Generate the validated biome-inorganic-resources.csv product from "
            "the four canonical Starfield datasets. Bundled project data is used "
            "by default; output defaults to ./output/."
        ),
        epilog=(
            "examples:\n"
            "  starfield-resource-reproducer\n"
            "  starfield-resource-reproducer --manifest\n"
            "  starfield-resource-reproducer --output C:\\Exports\n"
            "  starfield-resource-reproducer --output my-resources.csv --manifest\n"
            "  starfield-resource-reproducer --validate-only"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    detail = parser.add_mutually_exclusive_group()
    detail.add_argument(
        "--quiet", action="store_true", help="suppress normal informational output"
    )
    detail.add_argument(
        "--verbose", action="store_true", help="show resolved paths and stage details"
    )
    parser.add_argument(
        "--no-overwrite", action="store_true", help="fail if a requested artifact exists"
    )
    parser.add_argument(
        "--resource-generation-file", metavar="PATH",
        help="override planet-resource-generation.csv (relative to current directory)",
    )
    parser.add_argument(
        "--resource-tree-file", metavar="PATH",
        help="override ires-hierarchy.csv (relative to current directory)",
    )
    parser.add_argument(
        "--atmospheric-resources-file", metavar="PATH",
        help="override planet-atmospheric-resources.csv (relative to current directory)",
    )
    parser.add_argument(
        "--planet-directory-file", metavar="PATH",
        help="override planet-directory.csv (relative to current directory)",
    )
    parser.add_argument(
        "--output", metavar="PATH",
        help="output directory or explicit .csv filename (default: ./output/)",
    )
    parser.add_argument(
        "--manifest", action="store_true", help="write a sibling .manifest.json file"
    )
    parser.add_argument(
        "--validate-only", action="store_true",
        help="run the complete production validation pipeline without writing files",
    )
    return parser


def _absolute_from_cwd(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else Path.cwd() / path


def resolve_explicit_output(value: str) -> Path:
    """Resolve a user value as an output directory or explicit CSV filename."""

    path = _absolute_from_cwd(value)
    trailing_separator = value.endswith(tuple(
        separator for separator in (os.sep, os.altsep) if separator
    ))
    if path.exists():
        if path.is_dir():
            return path / OUTPUT_FILENAME
        if path.is_file() and path.suffix.lower() == ".csv":
            return path
        raise OutputPathUsageError("--output existing file must have a .csv suffix")
    if trailing_separator:
        return path / OUTPUT_FILENAME
    if path.suffix.lower() == ".csv":
        return path
    if path.suffix:
        raise OutputPathUsageError("--output filename must have a .csv suffix")
    return path / OUTPUT_FILENAME


def _directory_is_usable(directory: Path) -> bool:
    """Create a directory if needed and verify a temporary file can be written."""

    try:
        directory.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=directory, delete=True):
            pass
        return True
    except OSError:
        return False


def resolve_default_output(cwd: Path | None = None) -> tuple[Path, bool]:
    """Prefer ./output and report whether the caller-directory fallback was used."""

    caller_dir = Path.cwd() if cwd is None else Path(cwd)
    preferred = caller_dir / "output"
    if _directory_is_usable(preferred):
        return preferred / OUTPUT_FILENAME, False
    return caller_dir / OUTPUT_FILENAME, True


def _manifest_path(csv_path: Path) -> Path:
    return csv_path.with_suffix(".manifest.json")


def _input_paths(parsed: argparse.Namespace) -> dict[str, Path]:
    option_values = {
        "resource_generation_path": parsed.resource_generation_file,
        "resource_tree_path": parsed.resource_tree_file,
        "atmospheric_resources_path": parsed.atmospheric_resources_file,
        "planet_directory_path": parsed.planet_directory_file,
    }
    return {
        name: _absolute_from_cwd(value) if value is not None else _INPUT_DEFAULTS[name]
        for name, value in option_values.items()
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    parsed = parser.parse_args(sys.argv[1:] if argv is None else argv)
    if parsed.validate_only:
        incompatible = [
            option for enabled, option in (
                (parsed.output is not None, "--output"),
                (parsed.manifest, "--manifest"),
                (parsed.no_overwrite, "--no-overwrite"),
            ) if enabled
        ]
        if incompatible:
            parser.error("--validate-only cannot be used with " + ", ".join(incompatible))

    if parsed.output is not None:
        try:
            csv_path = resolve_explicit_output(parsed.output)
        except OutputPathUsageError as error:
            parser.error(str(error))
        fallback = False
    elif parsed.validate_only:
        csv_path = None
        fallback = False
    else:
        csv_path, fallback = resolve_default_output()

    manifest_path = _manifest_path(csv_path) if csv_path is not None else None
    write_manifest = bool(
        manifest_path is not None and (parsed.manifest or manifest_path.exists())
    )
    if parsed.no_overwrite and csv_path is not None:
        collisions = [csv_path] if csv_path.exists() else []
        if parsed.manifest and manifest_path is not None and manifest_path.exists():
            collisions.append(manifest_path)
        if collisions:
            print(
                "error: --no-overwrite collision: "
                + ", ".join(str(path) for path in collisions),
                file=sys.stderr,
            )
            return 1

    inputs = _input_paths(parsed)
    started = time.perf_counter()
    try:
        if parsed.verbose:
            print("Production inputs:")
            for path in inputs.values():
                print(f"  {path}")
            print("Stage: load and validate canonical inputs")
            print("Stage: generate, build, and validate product")
        prepared = prepare_product(
            **inputs,
            output_filename=csv_path.name if csv_path is not None else OUTPUT_FILENAME,
        )
        if not parsed.validate_only and csv_path is not None:
            write_prepared_product(
                prepared,
                csv_path,
                manifest_path=manifest_path if write_manifest else None,
            )
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    result = prepared.result
    if not parsed.quiet:
        if fallback:
            print(f"Could not use ./output; using {csv_path}")
        if parsed.validate_only:
            print(
                f"Validation succeeded: {len(result.rows)} rows "
                f"({result.biome_row_count} BIOME, "
                f"{result.atmosphere_row_count} ATMOSPHERE); no files written"
            )
        else:
            print(
                f"Wrote {len(result.rows)} rows "
                f"({result.biome_row_count} BIOME, "
                f"{result.atmosphere_row_count} ATMOSPHERE) to {csv_path}"
            )
            if write_manifest:
                action = "refreshed" if not parsed.manifest else "written"
                print(f"Manifest {action}: {manifest_path}")
        if parsed.verbose:
            print(
                "Input rows: "
                + ", ".join(
                    f"{item['filename']}={item['row_count']}"
                    for item in prepared.manifest["input_datasets"]
                )
            )
            print(f"Elapsed: {time.perf_counter() - started:.3f}s")
    return 0
