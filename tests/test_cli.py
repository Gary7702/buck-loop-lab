"""CLI subcommands actually run and write their outputs."""

from pathlib import Path

from buckloop.cli import main


def test_cli_step(tmp_path: Path) -> None:
    out = tmp_path / "dir with spaces"
    assert main(["step", "--setpoint", "9", "--duration", "0.002", "--out", str(out)]) == 0
    assert (out / "step_response.csv").stat().st_size > 0
    assert (out / "step_response.svg").read_text(encoding="utf-8").startswith("<svg")


def test_cli_bode(tmp_path: Path) -> None:
    out = tmp_path / "dir with spaces"
    assert main(["bode", "--n", "20", "--out", str(out)]) == 0
    assert (out / "bode.csv").stat().st_size > 0
    assert (out / "bode.svg").read_text(encoding="utf-8").startswith("<svg")


def test_cli_all(tmp_path: Path) -> None:
    out = tmp_path / "all"
    assert (
        main(
            [
                "all",
                "--setpoint",
                "8",
                "--duration",
                "0.002",
                "--n",
                "20",
                "--out",
                str(out),
            ]
        )
        == 0
    )
    for name in ("step_response.csv", "step_response.svg", "bode.csv", "bode.svg"):
        assert (out / name).stat().st_size > 0


def test_cli_help() -> None:
    try:
        main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0
