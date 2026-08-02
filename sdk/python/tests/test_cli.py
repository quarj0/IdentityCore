from __future__ import annotations

import pytest

from identitycore import __version__, cli


def test_help_is_structured_and_includes_examples(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["--help"])

    assert exc_info.value.code == 0
    output = capsys.readouterr().out
    assert "USAGE:" in output
    assert "COMMANDS:" in output
    assert "OPTIONS:" in output
    assert "EXAMPLES:" in output
    assert "completion" in output


@pytest.mark.parametrize(
    ("shell", "marker"),
    [("bash", "complete -F"), ("zsh", "compdef"), ("fish", "complete -c identitycore")],
)
def test_completion_generates_shell_script(
    shell: str, marker: str, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(["completion", shell]) == 0
    assert marker in capsys.readouterr().out


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["--version"])

    assert exc_info.value.code == 0
    assert capsys.readouterr().out == f"IdentityCore CLI {__version__}\n"
