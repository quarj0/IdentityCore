"""Small, scriptable command-line client for IdentityCore."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import stat
from pathlib import Path
from typing import Any

from identitycore.client import IdentityCoreClient
from identitycore.errors import IdentityCoreError


def _config_path() -> Path:
    return Path(
        os.environ.get(
            "IDENTITYCORE_CONFIG",
            Path.home() / ".config" / "identitycore" / "config.json",
        )
    )


def _load_config() -> dict[str, str]:
    path = _config_path()
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _save_config(config: dict[str, str]) -> None:
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)


def _client(args: argparse.Namespace) -> IdentityCoreClient:
    config = _load_config()
    api_origin = args.api_origin or os.environ.get("IDENTITYCORE_API_ORIGIN") or config.get("api_origin", "")
    client_id = args.client_id or os.environ.get("IDENTITYCORE_CLIENT_ID") or config.get("client_id", "")
    client_secret = args.client_secret or os.environ.get("IDENTITYCORE_CLIENT_SECRET") or config.get("client_secret", "")
    return IdentityCoreClient(
        api_origin=api_origin,
        client_id=client_id,
        client_secret=client_secret,
    )


def _print(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="identitycore", description="IdentityCore API command line client")
    parser.add_argument("--api-origin", help="API origin, or IDENTITYCORE_API_ORIGIN")
    parser.add_argument("--client-id", help="API client ID, or IDENTITYCORE_CLIENT_ID")
    parser.add_argument("--client-secret", help="API client secret, or IDENTITYCORE_CLIENT_SECRET")
    subparsers = parser.add_subparsers(dest="command", required=True)

    login = subparsers.add_parser("login", help="Store API credentials locally")
    login.add_argument("--api-origin", required=True)
    login.add_argument("--client-id", required=True)
    login.add_argument("--client-secret")

    subparsers.add_parser("health", help="Check API availability")

    policies = subparsers.add_parser("policies", help="Manage verification policies")
    policy_commands = policies.add_subparsers(dest="policy_command", required=True)
    policy_commands.add_parser("list", help="List active policies")
    policy_get = policy_commands.add_parser("get", help="Retrieve a policy")
    policy_get.add_argument("policy_id")

    verifications = subparsers.add_parser("verifications", help="Manage verifications")
    verification_commands = verifications.add_subparsers(dest="verification_command", required=True)
    verification_commands.add_parser("list", help="List verifications")
    verification_get = verification_commands.add_parser("get", help="Retrieve a verification")
    verification_get.add_argument("verification_id")
    verification_cancel = verification_commands.add_parser("cancel", help="Cancel a verification")
    verification_cancel.add_argument("verification_id")
    verification_cancel.add_argument("--reason", default="")
    verification_create = verification_commands.add_parser("create", help="Create a hosted verification")
    verification_create.add_argument("--purpose", required=True)
    verification_create.add_argument("--policy-id", required=True)
    verification_create.add_argument("--full-name", required=True)
    verification_create.add_argument("--email", required=True)
    verification_create.add_argument("--project-id", default="")
    verification_create.add_argument("--external-reference", default="")
    verification_create.add_argument("--redirect-url", default="")
    verification_create.add_argument("--idempotency-key", default="")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "login":
        client_secret = args.client_secret or getpass.getpass("IdentityCore client secret: ")
        if not client_secret:
            parser.error("client secret is required")
        _save_config(
            {
                "api_origin": args.api_origin,
                "client_id": args.client_id,
                "client_secret": client_secret,
            }
        )
        print(f"Credentials saved to {_config_path()}")
        return 0

    try:
        client = _client(args)
        if args.command == "health":
            _print(client.health())
        elif args.command == "policies":
            if args.policy_command == "list":
                _print(client.policies.list())
            else:
                _print(client.policies.retrieve(args.policy_id))
        elif args.command == "verifications":
            if args.verification_command == "list":
                _print(client.verifications.list())
            elif args.verification_command == "get":
                _print(client.verifications.retrieve(args.verification_id))
            elif args.verification_command == "cancel":
                _print(client.verifications.cancel(args.verification_id, reason=args.reason))
            else:
                _print(
                    client.verifications.create(
                        purpose=args.purpose,
                        policy_id=args.policy_id,
                        project_id=args.project_id,
                        external_reference=args.external_reference,
                        redirect_url=args.redirect_url,
                        verification_subject={"full_name": args.full_name, "email": args.email},
                        idempotency_key=args.idempotency_key,
                    )
                )
        return 0
    except IdentityCoreError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
