from __future__ import annotations

import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from identitycore import __version__, cli


class IdentityCoreCliTests(unittest.TestCase):
    def run_cli(self, *arguments: str) -> tuple[int, str]:
        output = io.StringIO()
        with redirect_stdout(output):
            try:
                result = cli.main(list(arguments))
            except SystemExit as exc:
                result = exc.code
        return result, output.getvalue()

    def test_help_is_structured_and_includes_examples(self) -> None:
        exit_code, output = self.run_cli("--help")

        self.assertEqual(exit_code, 0)
        self.assertIn("USAGE:", output)
        self.assertIn("COMMANDS:", output)
        self.assertIn("OPTIONS:", output)
        self.assertIn("EXAMPLES:", output)
        self.assertIn("completion", output)

    def test_completion_generates_shell_scripts(self) -> None:
        scripts = {
            "bash": "complete -F",
            "zsh": "compdef",
            "fish": "complete -c identitycore",
        }

        for shell, marker in scripts.items():
            with self.subTest(shell=shell):
                exit_code, output = self.run_cli("completion", shell)
                self.assertEqual(exit_code, 0)
                self.assertIn(marker, output)

    def test_version(self) -> None:
        exit_code, output = self.run_cli("--version")

        self.assertEqual(exit_code, 0)
        self.assertEqual(output, f"IdentityCore CLI {__version__}\n")


if __name__ == "__main__":
    unittest.main()
