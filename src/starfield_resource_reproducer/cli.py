import argparse
import sys
from collections.abc import Sequence

from starfield_resource_reproducer import __version__


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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    arguments = list(sys.argv[1:] if argv is None else argv)

    if not arguments:
        parser.print_help()
        return 0

    parser.parse_args(arguments)
    return 0
