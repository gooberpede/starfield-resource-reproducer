import pytest

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
    assert capsys.readouterr().out.strip() == "starfield-resource-reproducer 0.1.0"


def test_no_arguments_prints_help(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    assert "usage:" in capsys.readouterr().out


def test_validate_all_writes_report(tmp_path, capsys: pytest.CaptureFixture[str]) -> None:
    output = tmp_path / "full.csv"

    assert main(["--validate-all", "--output", str(output)]) == 0

    rendered = capsys.readouterr().out
    assert "Validation intersection: 1444" in rendered
    assert "Exact matches: 1281" in rendered
    assert output.read_text(encoding="utf-8").startswith("PlanetFormID,")
