from pathlib import Path
import tomllib

import starfield_resource_reproducer


def test_package_version() -> None:
    assert starfield_resource_reproducer.__version__ == "1.0.0"


def test_console_script_targets_production_cli() -> None:
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    metadata = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    assert metadata["project"]["scripts"]["starfield-resource-reproducer"] == (
        "starfield_resource_reproducer.cli:main"
    )
