import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from starfield_resource_reproducer import __version__
from starfield_resource_reproducer.load_data import load_project_data
from starfield_resource_reproducer.validation import (
    format_full_validation_summary,
    validate_all_planets,
    write_mismatch_csv,
)


_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="starfield-resource-reproducer",
        description="Reproduce Starfield planetary resource generation.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--validate-all",
        "--all",
        action="store_true",
        help="validate the complete generation/oracle inorganic intersection",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_PROJECT_ROOT / "validation" / "full-canonical-mismatches.csv",
        help="path for the machine-readable mismatch CSV",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=_PROJECT_ROOT / "data",
        help=argparse.SUPPRESS,
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    arguments = list(sys.argv[1:] if argv is None else argv)

    if not arguments:
        parser.print_help()
        return 0

    parsed = parser.parse_args(arguments)
    if parsed.validate_all:
        project_data = load_project_data(parsed.data_dir)
        result = validate_all_planets(project_data)
        write_mismatch_csv(result, parsed.output)
        print(format_full_validation_summary(result))
        print(f"Mismatch report: {parsed.output}")
    return 0
