import tomllib
from pathlib import Path


def test_pytest_default_command_stays_fast_and_coverage_gate_is_configured() -> None:
    config = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    addopts = config["tool"]["pytest"]["ini_options"]["addopts"]
    coverage_run = config["tool"]["coverage"]["run"]
    coverage_report = config["tool"]["coverage"]["report"]

    assert addopts == "-q"
    assert coverage_run["source"] == ["backend"]
    assert coverage_report["fail_under"] == 80
    assert coverage_report["show_missing"] is True
