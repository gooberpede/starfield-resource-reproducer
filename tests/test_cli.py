import pytest
from types import SimpleNamespace

from starfield_resource_reproducer.cli import main


def test_help_exits_successfully(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--help"])

    assert exit_info.value.code == 0
    assert "Reproduce Starfield planetary resource generation." in capsys.readouterr().out


def test_version_exits_successfully(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])

    assert exit_info.value.code == 0
    assert capsys.readouterr().out.strip() == "starfield-resource-reproducer 1.0.0"


def test_no_arguments_prints_help(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    assert "usage:" in capsys.readouterr().out


def test_validate_all_writes_report(tmp_path, capsys: pytest.CaptureFixture[str]) -> None:
    output = tmp_path / "full.csv"

    assert main(["--validate-all", "--output", str(output)]) == 0

    rendered = capsys.readouterr().out
    assert "Validation intersection: 1444" in rendered
    assert "Exact matches: 1444" in rendered
    assert "Final-set/provenance mismatches" not in rendered
    assert (
        "Full-corpus provenance comparison: not measurable "
        "(no independent expected-provenance oracle)"
    ) in rendered
    assert output.read_text(encoding="utf-8").startswith("PlanetFormID,")


def test_export_biome_resources_uses_fixed_product_path(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    called = []
    monkeypatch.setattr(
        "starfield_resource_reproducer.cli.export_default_product",
        lambda root: called.append(root) or SimpleNamespace(
            rows=tuple(range(7)), biome_row_count=5, atmosphere_row_count=2
        ),
    )

    assert main(["--export-biome-resources"]) == 0
    assert len(called) == 1
    assert "Exported 7 rows (5 BIOME, 2 ATMOSPHERE)" in capsys.readouterr().out
