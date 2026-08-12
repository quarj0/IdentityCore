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
            "bash": ("complete -F", "--purpose"),
            "zsh": ("compdef", "--purpose"),
            "fish": ("complete -c identitycore", "-l purpose"),
        }

        for shell, (marker, purpose_option) in scripts.items():
            with self.subTest(shell=shell):
                exit_code, output = self.run_cli("completion", shell)
                self.assertEqual(exit_code, 0)
                self.assertIn(marker, output)
                self.assertIn(purpose_option, output)
                self.assertIn("bash", output)

    def test_version(self) -> None:
        exit_code, output = self.run_cli("--version")

        self.assertEqual(exit_code, 0)
        self.assertEqual(output, f"IdentityCore CLI {__version__}\n")

    def test_named_profiles_are_saved_without_echoing_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"IDENTITYCORE_CONFIG": f"{directory}/config.json"}
        ):
            exit_code, _ = self.run_cli(
                "login",
                "--profile",
                "sandbox",
                "--environment",
                "sandbox",
                "--access-token",
                "top-secret",
            )
            self.assertEqual(exit_code, 0)
            exit_code, output = self.run_cli(
                "--profile", "sandbox", "profiles", "current"
            )

        self.assertEqual(exit_code, 0)
        self.assertNotIn("top-secret", output)
        self.assertTrue(json.loads(output)["authenticated"])

    def test_global_profile_is_preserved_for_login(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"IDENTITYCORE_CONFIG": f"{directory}/config.json"}, clear=False
        ):
            exit_code, _ = self.run_cli(
                "--profile",
                "sandbox",
                "login",
                "--environment",
                "sandbox",
                "--access-token",
                "token",
            )
            saved = json.loads(Path(f"{directory}/config.json").read_text())

        self.assertEqual(exit_code, 0)
        self.assertIn("sandbox", saved["profiles"])
        self.assertNotIn("default", saved["profiles"])

    def test_first_named_profile_migrates_legacy_default_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"IDENTITYCORE_CONFIG": f"{directory}/config.json"}, clear=False
        ):
            config_path = Path(f"{directory}/config.json")
            config_path.write_text(
                json.dumps(
                    {
                        "api_origin": "https://legacy.example.test",
                        "client_id": "legacy-client",
                        "client_secret": "legacy-secret",
                    }
                )
            )
            exit_code, _ = self.run_cli(
                "login",
                "--profile",
                "production",
                "--environment",
                "production",
                "--access-token",
                "token",
            )
            saved = json.loads(config_path.read_text())

        self.assertEqual(exit_code, 0)
        self.assertEqual(saved["profiles"]["default"]["client_id"], "legacy-client")
        self.assertIn("production", saved["profiles"])

    def test_explicit_environment_overrides_saved_origin(self) -> None:
        args = cli._build_parser().parse_args(["--environment", "production", "health"])
        with patch.object(
            cli,
            "_load_config",
            return_value={
                "profiles": {
                    "default": {
                        "environment": "sandbox",
                        "api_origin": "https://saved.invalid",
                        "access_token": "token",
                    }
                }
            },
        ):
            client = cli._client(args)

        self.assertEqual(client.api_origin, "https://api.identitycore.com")

    def test_table_output_and_supported_project_filters_are_forwarded(self) -> None:
        calls: list[tuple[str, str]] = []

        class Client:
            def request(self, method: str, path: str):
                calls.append((method, path))
                return {"results": [{"id": "prj_1", "environment": "sandbox"}]}

        output = io.StringIO()
        with patch.object(cli, "_client", return_value=Client()), redirect_stdout(
            output
        ):
            exit_code = cli.main(
                [
                    "--output",
                    "table",
                    "projects",
                    "list",
                    "--page-size",
                    "25",
                    "--environment",
                    "sandbox",
                ]
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            calls, [("GET", "/projects/?page_size=25&environment=sandbox")]
        )
        self.assertIn("ENVIRONMENT", output.getvalue())

    def test_project_actions_and_webhook_payloads_match_backend_contract(self) -> None:
        calls = []

        class Client:
            def request(self, method, path, body=None):
                calls.append((method, path, body))
                return {}

        with patch.object(cli, "_client", return_value=Client()):
            self.assertEqual(cli.main(["projects", "disable", "prj_1"]), 0)
            self.assertEqual(
                cli.main(
                    [
                        "webhooks",
                        "create",
                        "--url",
                        "https://example.com/hook",
                        "--event",
                        "verification.completed",
                    ]
                ),
                0,
            )
            self.assertEqual(cli.main(["webhooks", "test", "wh_1"]), 0)

        self.assertEqual(calls[0], ("POST", "/projects/prj_1/suspend", {}))
        self.assertNotIn("project_id", calls[1][2])
        self.assertEqual(calls[2], ("POST", "/webhook-endpoints/wh_1/test", {}))

    def test_api_client_create_requires_a_scope(self) -> None:
        exit_code, _ = self.run_cli(
            "api-clients", "create", "--name", "CLI", "--project-id", "prj_1"
        )

        self.assertEqual(exit_code, 2)

    def test_api_errors_are_structured_on_stderr(self) -> None:
        error = io.StringIO()
        with patch.object(
            cli,
            "_client",
            side_effect=cli.IdentityCoreAPIError(
                "No access", code="forbidden", status=403, request_id="req_1"
            ),
        ), redirect_stderr(error):
            exit_code = cli.main(["health"])

        payload = json.loads(error.getvalue())
        self.assertEqual(exit_code, 2)
        self.assertEqual(payload["error"]["code"], "forbidden")
        self.assertEqual(payload["error"]["request_id"], "req_1")


if __name__ == "__main__":
    unittest.main()
