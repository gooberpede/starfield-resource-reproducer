"""Regression tests for the repository mojibake guardrail."""

import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_mojibake.py"


def test_tracked_repository_text_is_clean() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_guard_rejects_marker_and_accepts_clean_utf8(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture.txt"
    marker = "\u00d4\u00c7\u00f6"
    fixture.write_text(f"clean line\ncorrupt {marker} text\n", encoding="utf-8")

    rejected = subprocess.run(
        [sys.executable, str(SCRIPT), str(fixture)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert rejected.returncode == 1
    assert f"{fixture.as_posix()}:2:" in rejected.stdout
    assert "\\xd4\\xc7\\xf6" in rejected.stdout

    fixture.write_text("clean line\nvalid em dash \u2014 text\n", encoding="utf-8")
    accepted = subprocess.run(
        [sys.executable, str(SCRIPT), str(fixture)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert accepted.returncode == 0
    assert accepted.stdout.strip() == "Mojibake check passed."
