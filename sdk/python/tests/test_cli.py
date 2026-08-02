from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

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

    def test_named_profiles_are_saved_without_echoing_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"IDENTITYCORE_CONFIG": f"{directory}/config.json"}
        ):
            exit_code, _ = self.run_cli(
                "login", "--profile", "sandbox", "--environment", "sandbox",
                "--access-token", "top-secret",
            )
            self.assertEqual(exit_code, 0)
            exit_code, output = self.run_cli("--profile", "sandbox", "profiles", "current")

        self.assertEqual(exit_code, 0)
        self.assertNotIn("top-secret", output)
        self.assertTrue(json.loads(output)["authenticated"])

    def test_table_output_and_pagination_are_forwarded(self) -> None:
        calls: list[tuple[str, str]] = []

        class Client:
            def request(self, method: str, path: str):
                calls.append((method, path))
                return {"results": [{"id": "prj_1", "environment": "sandbox"}]}

        output = io.StringIO()
        with patch.object(cli, "_client", return_value=Client()), redirect_stdout(output):
            exit_code = cli.main(["--output", "table", "projects", "list", "--limit", "25", "--environment", "sandbox"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(calls, [("GET", "/projects/?limit=25&environment=sandbox")])
        self.assertIn("ENVIRONMENT", output.getvalue())

    def test_api_errors_are_structured_on_stderr(self) -> None:
        error = io.StringIO()
        with patch.object(cli, "_client", side_effect=cli.IdentityCoreAPIError(
            "No access", code="forbidden", status=403, request_id="req_1"
        )), redirect_stderr(error):
            exit_code = cli.main(["health"])

        payload = json.loads(error.getvalue())
        self.assertEqual(exit_code, 2)
        self.assertEqual(payload["error"]["code"], "forbidden")
        self.assertEqual(payload["error"]["request_id"], "req_1")


if __name__ == "__main__":
    unittest.main()
