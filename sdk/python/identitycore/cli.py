"""Small, scriptable command-line client for IdentityCore."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import stat
from pathlib import Path
from typing import Any

from identitycore.client import IdentityCoreClient, __version__
from identitycore.errors import IdentityCoreError


class _HelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Keep examples readable and give option descriptions room to breathe."""

    def __init__(self, prog: str) -> None:
        super().__init__(prog, max_help_position=30, width=100)


class _ArgumentParser(argparse.ArgumentParser):
    """An ArgumentParser with the compact, uppercase sections common to Unix tools."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("formatter_class", _HelpFormatter)
        super().__init__(*args, **kwargs)

    def format_help(self) -> str:
        help_text = super().format_help()
        headings = {
            "usage:": "USAGE:\n ",
            "positional arguments:\n": "COMMANDS:\n",
            "options:\n": "OPTIONS:\n",
        }
        for original, replacement in headings.items():
            help_text = help_text.replace(original, replacement)
        return help_text


def _completion_script(shell: str) -> str:
    """Return a dependency-free completion definition for a supported shell."""
    if shell == "bash":
        return r'''# bash completion for identitycore
_identitycore_completion() {
    local cur prev path
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    path=" ${COMP_WORDS[*]:1:COMP_CWORD-1} "

    case "$prev" in
        --api-origin|--client-id|--client-secret|--policy-id|--purpose|--full-name|--email|--project-id|--external-reference|--redirect-url|--idempotency-key|--reason)
            return ;;
    esac
    case "$path" in
        *" verifications create "*) opts="--purpose --policy-id --full-name --email --project-id --external-reference --redirect-url --idempotency-key --help" ;;
        *" verifications cancel "*) opts="--reason --help" ;;
        *" verifications "*) opts="list get cancel create --help" ;;
        *" policies "*) opts="list get --help" ;;
        *" login "*) opts="--api-origin --client-id --client-secret --help" ;;
        *" completion "*) opts="bash zsh fish --help" ;;
        *) opts="login health policies verifications completion --api-origin --client-id --client-secret --version --help" ;;
    esac
    COMPREPLY=( $(compgen -W "$opts" -- "$cur") )
}
complete -F _identitycore_completion identitycore'''
    if shell == "zsh":
        return r'''#compdef identitycore
_identitycore() {
  local -a commands
  commands=(
    'login:Store API credentials locally'
    'health:Check API availability'
    'policies:Manage verification policies'
    'verifications:Manage verifications'
    'completion:Generate shell completion setup'
  )
  _arguments -C \
    '--api-origin[API origin]:origin' \
    '--client-id[API client ID]:client id' \
    '--client-secret[API client secret]:client secret' \
    '--version[show version]' '*::arg:->args'
  case $words[1] in
    policies) _values 'policy command' list get ;;
    verifications) _values 'verification command' list get cancel create ;;
    completion) _values shell bash zsh fish ;;
    *) _describe command commands ;;
  esac
}
compdef _identitycore identitycore'''
    return r'''# fish completion for identitycore
complete -c identitycore -f
complete -c identitycore -n '__fish_use_subcommand' -a 'login' -d 'Store API credentials locally'
complete -c identitycore -n '__fish_use_subcommand' -a 'health' -d 'Check API availability'
complete -c identitycore -n '__fish_use_subcommand' -a 'policies' -d 'Manage verification policies'
complete -c identitycore -n '__fish_use_subcommand' -a 'verifications' -d 'Manage verifications'
complete -c identitycore -n '__fish_use_subcommand' -a 'completion' -d 'Generate shell completion setup'
complete -c identitycore -n '__fish_seen_subcommand_from policies' -a 'list get'
complete -c identitycore -n '__fish_seen_subcommand_from verifications' -a 'list get cancel create'
complete -c identitycore -n '__fish_seen_subcommand_from completion' -a 'bash zsh fish'
complete -c identitycore -l api-origin -r -d 'API origin'
complete -c identitycore -l client-id -r -d 'API client ID'
complete -c identitycore -l client-secret -r -d 'API client secret'
complete -c identitycore -n '__fish_seen_subcommand_from create' -l purpose -r -d 'Verification purpose'
complete -c identitycore -n '__fish_seen_subcommand_from create' -l policy-id -r -d 'Policy ID'
complete -c identitycore -n '__fish_seen_subcommand_from create' -l full-name -r -d 'Subject full name'
complete -c identitycore -n '__fish_seen_subcommand_from create' -l email -r -d 'Subject email'
complete -c identitycore -n '__fish_seen_subcommand_from create' -l project-id -r -d 'Project ID'
complete -c identitycore -n '__fish_seen_subcommand_from create' -l external-reference -r -d 'External reference'
complete -c identitycore -n '__fish_seen_subcommand_from create' -l redirect-url -r -d 'Completion redirect URL'
complete -c identitycore -n '__fish_seen_subcommand_from create' -l idempotency-key -r -d 'Idempotency key'
complete -c identitycore -n '__fish_seen_subcommand_from cancel' -l reason -r -d 'Cancellation reason' '''


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
    parser = _ArgumentParser(
        prog="identitycore",
        description="IdentityCore API command line client\n\nSecurely manage policies and verifications from your terminal.",
        epilog="""EXAMPLES:
  identitycore login --api-origin https://api.identitycore.com --client-id cli_...
  identitycore policies list
  identitycore verifications get ver_...
  identitycore completion bash >> ~/.bashrc

Run 'identitycore COMMAND --help' for command-specific options.
Documentation: https://docs.identitycore.com""",
        formatter_class=_HelpFormatter,
    )
    parser.add_argument("--api-origin", help="API origin, or IDENTITYCORE_API_ORIGIN")
    parser.add_argument("--client-id", help="API client ID, or IDENTITYCORE_CLIENT_ID")
    parser.add_argument("--client-secret", help="API client secret, or IDENTITYCORE_CLIENT_SECRET")
    parser.add_argument("--version", action="version", version=f"IdentityCore CLI {__version__}")
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
    completion = subparsers.add_parser("completion", help="Generate shell completion setup")
    completion.add_argument("shell", choices=("bash", "zsh", "fish"), help="Shell to generate completion for")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "completion":
        print(_completion_script(args.shell))
        return 0

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
