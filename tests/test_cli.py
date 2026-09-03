"""Focused parser, path, artifact-policy, and production CLI regressions."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from starfield_resource_reproducer.cli import (
    OUTPUT_FILENAME,
    main,
    resolve_default_output,
    resolve_explicit_output,
)


@pytest.fixture
def fake_production(monkeypatch: pytest.MonkeyPatch):
    calls: list[dict[str, object]] = []
    result = SimpleNamespace(rows=tuple(range(7)), biome_row_count=5, atmosphere_row_count=2)
    manifest = {
        "export_timestamp": "2026-09-03T00:00:00Z",
        "input_datasets": [{"filename": "input.csv", "row_count": 11}],
    }

    def prepare(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(
            result=result,
            manifest=manifest,
            csv_text="new csv\n",
            manifest_text=json.dumps(manifest) + "\n",
        )

    def write(prepared, csv_path, *, manifest_path=None):
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        csv_path.write_text(prepared.csv_text, encoding="utf-8")
        if manifest_path is not None:
            manifest_path.write_text(prepared.manifest_text, encoding="utf-8")

    monkeypatch.setattr("starfield_resource_reproducer.cli.prepare_product", prepare)
    monkeypatch.setattr("starfield_resource_reproducer.cli.write_prepared_product", write)
    return calls


def test_help_and_version_exit_successfully(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as help_exit:
        main(["--help"])
    assert help_exit.value.code == 0
    assert "biome-inorganic-resources.csv" in capsys.readouterr().out

    with pytest.raises(SystemExit) as version_exit:
        main(["--version"])
    assert version_exit.value.code == 0
    assert capsys.readouterr().out.strip() == "starfield-resource-reproducer 1.0.0"


def test_help_exposes_only_the_baseline_public_surface(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit):
        main(["--help"])
    help_text = capsys.readouterr().out
    for option in (
        "--quiet", "--verbose", "--no-overwrite",
        "--resource-generation-file", "--resource-tree-file",
        "--atmospheric-resources-file", "--planet-directory-file",
        "--output", "--manifest", "--validate-only",
    ):
        assert option in help_text
    for legacy in (
        "--validate-all", "--export-biome-resources", "--data-dir",
        "--atmosphere-data", "--diagnostic-mode",
    ):
        assert legacy not in help_text


@pytest.mark.parametrize(
    "arguments",
    [
        ["--unknown"],
        ["--output"],
        ["--quiet", "--verbose"],
        ["--validate-only", "--output", "somewhere"],
        ["--validate-only", "--manifest"],
        ["--validate-only", "--no-overwrite"],
        ["--output", "wrong.txt"],
    ],
)
def test_usage_errors_exit_two(arguments: list[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(arguments)
    assert exit_info.value.code == 2


def test_output_path_resolution_forms(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    existing = tmp_path / "existing"
    existing.mkdir()
    existing_csv = tmp_path / "existing.csv"
    existing_csv.write_text("old", encoding="utf-8")

    assert resolve_explicit_output(str(existing)) == existing / OUTPUT_FILENAME
    assert resolve_explicit_output("new-directory") == tmp_path / "new-directory" / OUTPUT_FILENAME
    assert resolve_explicit_output("custom.CSV") == tmp_path / "custom.CSV"
    assert resolve_explicit_output(str(existing_csv)) == existing_csv
    assert resolve_explicit_output(str(tmp_path / "nested" / "exact.csv")) == tmp_path / "nested" / "exact.csv"


def test_default_output_prefers_output_and_can_fall_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path, fallback = resolve_default_output(tmp_path)
    assert path == tmp_path / "output" / OUTPUT_FILENAME
    assert not fallback

    monkeypatch.setattr("starfield_resource_reproducer.cli._directory_is_usable", lambda path: False)
    path, fallback = resolve_default_output(tmp_path)
    assert path == tmp_path / OUTPUT_FILENAME
    assert fallback


def test_bare_run_writes_default_csv_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake_production
) -> None:
    monkeypatch.chdir(tmp_path)
    assert main([]) == 0
    assert (tmp_path / "output" / OUTPUT_FILENAME).read_text(encoding="utf-8") == "new csv\n"
    assert not (tmp_path / "output" / "biome-inorganic-resources.manifest.json").exists()


def test_explicit_directory_and_custom_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake_production
) -> None:
    monkeypatch.chdir(tmp_path)
    assert main(["--output", "exports", "--manifest"]) == 0
    assert (tmp_path / "exports" / OUTPUT_FILENAME).exists()

    assert main(["--output", "other/custom.csv", "--manifest"]) == 0
    assert (tmp_path / "other" / "custom.csv").exists()
    assert (tmp_path / "other" / "custom.manifest.json").exists()
    assert fake_production[-1]["output_filename"] == "custom.csv"


def test_default_overwrite_and_no_overwrite_collision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake_production,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "target.csv"
    target.write_text("old", encoding="utf-8")
    assert main(["--output", str(target)]) == 0
    assert target.read_text(encoding="utf-8") == "new csv\n"

    target.write_text("preserve", encoding="utf-8")
    assert main(["--output", str(target), "--no-overwrite"]) == 1
    assert target.read_text(encoding="utf-8") == "preserve"
    assert "collision" in capsys.readouterr().err


def test_manifest_refresh_and_no_overwrite_rules(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake_production
) -> None:
    monkeypatch.chdir(tmp_path)
    csv_path = tmp_path / "product.csv"
    manifest_path = tmp_path / "product.manifest.json"
    manifest_path.write_text("stale", encoding="utf-8")

    assert main(["--output", str(csv_path)]) == 0
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["export_timestamp"] == "2026-09-03T00:00:00Z"

    csv_path.unlink()
    manifest_path.write_text("stale again", encoding="utf-8")
    assert main(["--output", str(csv_path), "--no-overwrite"]) == 0
    assert "stale again" not in manifest_path.read_text(encoding="utf-8")

    csv_path.unlink()
    manifest_path.write_text("preserve", encoding="utf-8")
    assert main(["--output", str(csv_path), "--manifest", "--no-overwrite"]) == 1
    assert not csv_path.exists()
    assert manifest_path.read_text(encoding="utf-8") == "preserve"


def test_validate_only_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake_production
) -> None:
    monkeypatch.chdir(tmp_path)
    assert main(["--validate-only"]) == 0
    assert not (tmp_path / "output").exists()
    assert len(fake_production) == 1


def test_input_overrides_resolve_relative_to_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake_production
) -> None:
    monkeypatch.chdir(tmp_path)
    options = {
        "--resource-generation-file": "generation.csv",
        "--resource-tree-file": "tree.csv",
        "--atmospheric-resources-file": "atmosphere.csv",
        "--planet-directory-file": "directory.csv",
    }
    arguments = [item for pair in options.items() for item in pair]
    assert main([*arguments, "--validate-only"]) == 0
    assert fake_production[0]["resource_generation_path"] == tmp_path / "generation.csv"
    assert fake_production[0]["resource_tree_path"] == tmp_path / "tree.csv"
    assert fake_production[0]["atmospheric_resources_path"] == tmp_path / "atmosphere.csv"
    assert fake_production[0]["planet_directory_path"] == tmp_path / "directory.csv"


def test_runtime_error_is_concise_and_quiet_keeps_error(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        "starfield_resource_reproducer.cli.prepare_product",
        lambda **kwargs: (_ for _ in ()).throw(ValueError("bad input.csv")),
    )
    assert main(["--validate-only", "--quiet"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.strip() == "error: bad input.csv"


@pytest.mark.parametrize(
    ("option", "keyword"),
    [
        ("--resource-generation-file", "resource_generation_path"),
        ("--resource-tree-file", "resource_tree_path"),
        ("--atmospheric-resources-file", "atmospheric_resources_path"),
        ("--planet-directory-file", "planet_directory_path"),
    ],
)
def test_missing_explicit_input_fails_without_default_fallback(
    option: str,
    keyword: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)

    def fail(**kwargs):
        assert kwargs[keyword] == tmp_path / "missing.csv"
        raise ValueError(f"{kwargs[keyword]}: could not read canonical data")

    monkeypatch.setattr("starfield_resource_reproducer.cli.prepare_product", fail)
    assert main([option, "missing.csv", "--validate-only"]) == 1
    assert str(tmp_path / "missing.csv") in capsys.readouterr().err


def test_explicit_output_write_failure_does_not_fall_back(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_production,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "starfield_resource_reproducer.cli.write_prepared_product",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("access denied")),
    )
    assert main(["--output", "requested/result.csv"]) == 1
    assert "access denied" in capsys.readouterr().err
    assert not (tmp_path / "output" / OUTPUT_FILENAME).exists()


def test_quiet_suppresses_success_output(
    fake_production, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["--validate-only", "--quiet"]) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_verbose_paths_without_generation_diagnostics(
    fake_production, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["--validate-only", "--verbose"]) == 0
    output = capsys.readouterr().out
    assert "Production inputs:" in output
    assert "Stage:" in output
    assert "Input rows:" in output
    assert "RNG" not in output
