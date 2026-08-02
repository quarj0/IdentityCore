"""Production command-line client for IdentityCore."""
from __future__ import annotations

import argparse
import getpass
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode

from identitycore.client import IdentityCoreClient, __version__
from identitycore.errors import IdentityCoreAPIError, IdentityCoreError

ENVIRONMENTS = {
    "sandbox": "https://sandbox.api.identitycore.com",
    "production": "https://api.identitycore.com",
}
COMMANDS = {
    "projects": "list get create enable disable",
    "api-clients": "list get create rotate revoke",
    "workflows": "list get create publish archive clone versions",
    "templates": "list get",
    "webhooks": "list get create test disable reactivate",
    "verifications": "list get create cancel evidence",
    "policies": "list get",
}


class _HelpFormatter(argparse.RawDescriptionHelpFormatter):
    def __init__(self, prog: str) -> None:
        super().__init__(prog, max_help_position=30, width=100)


class _ArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("formatter_class", _HelpFormatter)
        super().__init__(*args, **kwargs)

    def format_help(self) -> str:
        text = super().format_help()
        for old, new in {"usage:": "USAGE:\n ", "positional arguments:\n": "COMMANDS:\n", "options:\n": "OPTIONS:\n"}.items():
            text = text.replace(old, new)
        return text


def _config_path() -> Path:
    return Path(os.environ.get("IDENTITYCORE_CONFIG", Path.home() / ".config" / "identitycore" / "config.json"))


def _load_config() -> dict[str, Any]:
    try:
        value = json.loads(_config_path().read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _save_config(config: dict[str, Any]) -> None:
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)


def _profile(config: dict[str, Any], name: str) -> dict[str, str]:
    profiles = config.get("profiles")
    if isinstance(profiles, dict):
        value = profiles.get(name, {})
        return value if isinstance(value, dict) else {}
    # Read the pre-profile configuration format for backwards compatibility.
    return {key: str(config.get(key, "")) for key in ("api_origin", "client_id", "client_secret")}


def _client(args: argparse.Namespace) -> IdentityCoreClient:
    config = _profile(_load_config(), args.profile)
    environment = args.environment or os.environ.get("IDENTITYCORE_ENVIRONMENT") or config.get("environment", "")
    origin = args.api_origin or os.environ.get("IDENTITYCORE_API_ORIGIN") or config.get("api_origin", "") or ENVIRONMENTS.get(environment, "")
    return IdentityCoreClient(
        api_origin=origin,
        client_id=args.client_id or os.environ.get("IDENTITYCORE_CLIENT_ID") or config.get("client_id", ""),
        client_secret=args.client_secret or os.environ.get("IDENTITYCORE_CLIENT_SECRET") or config.get("client_secret", ""),
        access_token=args.access_token or os.environ.get("IDENTITYCORE_ACCESS_TOKEN") or config.get("access_token", ""),
    )


def _scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value, separators=(",", ":"), sort_keys=True)
    return str(value)


def _print(value: Any, output: str = "json") -> None:
    if output == "json":
        print(json.dumps(value, indent=2, sort_keys=True))
        return
    rows = value.get("results", []) if isinstance(value, dict) and isinstance(value.get("results"), list) else value
    if not isinstance(rows, list):
        rows = [rows]
    rows = [row if isinstance(row, dict) else {"value": row} for row in rows]
    if not rows:
        return
    columns = list(dict.fromkeys(key for row in rows for key in row))
    widths = {key: max(len(key), *(len(_scalar(row.get(key))) for row in rows)) for key in columns}
    print("  ".join(key.upper().ljust(widths[key]) for key in columns))
    print("  ".join("-" * widths[key] for key in columns))
    for row in rows:
        print("  ".join(_scalar(row.get(key)).ljust(widths[key]) for key in columns))


def _query(**values: Any) -> str:
    values = {key: value for key, value in values.items() if value not in (None, "")}
    return "?" + urlencode(values, doseq=True) if values else ""


def _json_object(raw: str, option: str) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise IdentityCoreError(f"{option} must be valid JSON: {exc.msg}.") from exc
    if not isinstance(value, dict):
        raise IdentityCoreError(f"{option} must be a JSON object.")
    return value


def _list_flags(parser: argparse.ArgumentParser, *, status: bool = True) -> None:
    parser.add_argument("--cursor")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--page", type=int)
    parser.add_argument("--page-size", type=int)
    if status:
        parser.add_argument("--status")


def _resource(subparsers: Any, name: str, help_text: str) -> Any:
    parser = subparsers.add_parser(name, help=help_text)
    return parser.add_subparsers(dest=f"{name.replace('-', '_')}_command", required=True)


def _build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(
        prog="identitycore",
        description="IdentityCore API command line client\n\nManage IdentityCore resources interactively or in CI.",
        epilog="""EXAMPLES:
  identitycore login --profile sandbox --environment sandbox --client-id cli_...
  identitycore --profile production --output table projects list
  identitycore --access-token "$IDENTITYCORE_ACCESS_TOKEN" api-clients rotate apc_...
  identitycore completion bash >> ~/.bashrc

Documentation: https://docs.identitycore.com/cli""",
    )
    parser.add_argument("--profile", default=os.environ.get("IDENTITYCORE_PROFILE", "default"), help="Configuration profile (default: default)")
    parser.add_argument("--environment", choices=tuple(ENVIRONMENTS), help="Use the sandbox or production API origin")
    parser.add_argument("--api-origin", help="API origin, or IDENTITYCORE_API_ORIGIN")
    parser.add_argument("--client-id", help="API client ID, or IDENTITYCORE_CLIENT_ID")
    parser.add_argument("--client-secret", help="API client secret, or IDENTITYCORE_CLIENT_SECRET")
    parser.add_argument("--access-token", help="User access token, or IDENTITYCORE_ACCESS_TOKEN")
    parser.add_argument("--output", choices=("json", "table"), default=os.environ.get("IDENTITYCORE_OUTPUT", "json"))
    parser.add_argument("--version", action="version", version=f"IdentityCore CLI {__version__}")
    subs = parser.add_subparsers(dest="command", required=True)

    login = subs.add_parser("login", help="Save a named configuration profile")
    login.add_argument("--profile", default="default")
    login.add_argument("--environment", choices=tuple(ENVIRONMENTS))
    login.add_argument("--api-origin")
    login.add_argument("--client-id")
    login.add_argument("--client-secret")
    login.add_argument("--access-token")
    profiles = _resource(subs, "profiles", "Manage sandbox and production profiles")
    profiles.add_parser("list")
    profiles.add_parser("current")
    delete_profile = profiles.add_parser("delete")
    delete_profile.add_argument("name")
    subs.add_parser("health", help="Check API availability")

    policies = _resource(subs, "policies", "Manage verification policies")
    pl = policies.add_parser("list"); _list_flags(pl)
    pg = policies.add_parser("get"); pg.add_argument("policy_id")

    verifications = _resource(subs, "verifications", "Manage verifications and evidence")
    vl = verifications.add_parser("list"); _list_flags(vl); vl.add_argument("--external-reference")
    vg = verifications.add_parser("get"); vg.add_argument("verification_id")
    vc = verifications.add_parser("cancel"); vc.add_argument("verification_id"); vc.add_argument("--reason", default="")
    vn = verifications.add_parser("create")
    for flag in ("purpose", "policy-id", "full-name", "email"):
        vn.add_argument(f"--{flag}", required=True)
    for flag in ("project-id", "external-reference", "redirect-url", "idempotency-key"):
        vn.add_argument(f"--{flag}", default="")
    ve = verifications.add_parser("evidence", help="Download an evidence report")
    ve.add_argument("verification_id"); ve.add_argument("--file", required=True); ve.add_argument("--pdf", action="store_true")

    projects = _resource(subs, "projects", "Manage projects and environments")
    pjl = projects.add_parser("list"); _list_flags(pjl); pjl.add_argument("--environment", choices=tuple(ENVIRONMENTS))
    pjg = projects.add_parser("get"); pjg.add_argument("project_id")
    pjc = projects.add_parser("create"); pjc.add_argument("--name", required=True); pjc.add_argument("--environment", choices=tuple(ENVIRONMENTS), required=True); pjc.add_argument("--description", default="")
    for action in ("enable", "disable"):
        p = projects.add_parser(action); p.add_argument("project_id")

    clients = _resource(subs, "api-clients", "Create, rotate, and revoke API clients")
    acl = clients.add_parser("list"); _list_flags(acl)
    acg = clients.add_parser("get"); acg.add_argument("api_client_id")
    acc = clients.add_parser("create"); acc.add_argument("--name", required=True); acc.add_argument("--project-id", required=True); acc.add_argument("--scopes", action="append", default=[]); acc.add_argument("--allowed-network", action="append", default=[])
    for action in ("rotate", "revoke"):
        p = clients.add_parser(action); p.add_argument("api_client_id")

    workflows = _resource(subs, "workflows", "Manage workflows")
    wl = workflows.add_parser("list"); _list_flags(wl, status=False); wl.add_argument("--project-id")
    wg = workflows.add_parser("get"); wg.add_argument("workflow_id")
    wc = workflows.add_parser("create"); wc.add_argument("--name", required=True); wc.add_argument("--project-id", required=True); wc.add_argument("--definition", default="{}", help="Workflow fields as a JSON object")
    for action in ("publish", "archive", "clone", "versions"):
        p = workflows.add_parser(action); p.add_argument("workflow_id")

    templates = _resource(subs, "templates", "Browse workflow templates")
    tl = templates.add_parser("list"); _list_flags(tl, status=False); tl.add_argument("--category"); tl.add_argument("--search")
    tg = templates.add_parser("get"); tg.add_argument("template_id")

    webhooks = _resource(subs, "webhooks", "Manage and test webhook endpoints")
    whl = webhooks.add_parser("list"); _list_flags(whl)
    whg = webhooks.add_parser("get"); whg.add_argument("webhook_id")
    whc = webhooks.add_parser("create"); whc.add_argument("--url", required=True); whc.add_argument("--event", action="append", required=True); whc.add_argument("--project-id"); whc.add_argument("--description", default="")
    wht = webhooks.add_parser("test"); wht.add_argument("webhook_id"); wht.add_argument("--event", default="verification.completed"); wht.add_argument("--payload", default="{}")
    for action in ("disable", "reactivate"):
        p = webhooks.add_parser(action); p.add_argument("webhook_id")

    completion = subs.add_parser("completion", help="Generate shell autocomplete")
    completion.add_argument("shell", choices=("bash", "zsh", "fish"))
    return parser


def _completion_script(shell: str) -> str:
    top = "login profiles health policies verifications projects api-clients workflows templates webhooks completion"
    if shell == "bash":
        cases = "\n".join(f'      {name}) opts="{actions}" ;;' for name, actions in COMMANDS.items())
        return f'''# bash completion for identitycore
_identitycore_completion() {{
  local cur prev resource opts
  cur="${{COMP_WORDS[COMP_CWORD]}}"
  resource="${{COMP_WORDS[1]}}"
  case "$resource" in
{cases}
      *) opts="{top} --profile --environment --api-origin --client-id --client-secret --access-token --output --help --version" ;;
  esac
  COMPREPLY=( $(compgen -W "$opts" -- "$cur") )
}}
complete -F _identitycore_completion identitycore'''
    if shell == "zsh":
        descriptions = " ".join(f"'{name}:{name.replace('-', ' ')} commands'" for name in top.split())
        return f'''#compdef identitycore
_identitycore() {{
  local -a commands
  commands=({descriptions})
  _arguments -C '--profile[configuration profile]:profile' '--environment[API environment]:(sandbox production)' '--output[output format]:(json table)' '*::arg:->args'
  case $words[1] in
''' + "\n".join(f"    {name}) _values action {actions} ;;" for name, actions in COMMANDS.items()) + '''
    *) _describe command commands ;;
  esac
}
compdef _identitycore identitycore'''
    lines = ["# fish completion for identitycore", "complete -c identitycore -f"]
    lines += [f"complete -c identitycore -n '__fish_use_subcommand' -a '{name}'" for name in top.split()]
    for name, actions in COMMANDS.items():
        lines.append(f"complete -c identitycore -n '__fish_seen_subcommand_from {name}' -a '{actions}'")
    lines += ["complete -c identitycore -l profile -r", "complete -c identitycore -l environment -a 'sandbox production'", "complete -c identitycore -l output -a 'json table'"]
    return "\n".join(lines)


def _pagination(args: argparse.Namespace) -> str:
    return _query(cursor=getattr(args, "cursor", ""), limit=getattr(args, "limit", None), page=getattr(args, "page", None), page_size=getattr(args, "page_size", None), status=getattr(args, "status", ""))


def _dispatch(client: IdentityCoreClient, args: argparse.Namespace) -> Any:
    command = args.command
    action = getattr(args, f"{command.replace('-', '_')}_command", "")
    if command == "health":
        return client.health()
    if command == "policies":
        return client.request("GET", "/policies/" + (_pagination(args) if action == "list" else args.policy_id))
    if command == "verifications":
        if action == "list":
            return client.request("GET", "/verifications/" + _query(cursor=args.cursor, limit=args.limit, page=args.page, page_size=args.page_size, status=args.status, external_reference=args.external_reference))
        if action == "get": return client.verifications.retrieve(args.verification_id)
        if action == "cancel": return client.verifications.cancel(args.verification_id, reason=args.reason)
        if action == "create":
            return client.verifications.create(purpose=args.purpose, policy_id=args.policy_id, project_id=args.project_id, external_reference=args.external_reference, redirect_url=args.redirect_url, verification_subject={"full_name": args.full_name, "email": args.email}, idempotency_key=args.idempotency_key)
        suffix = "/download.pdf" if args.pdf else "/download"
        data = client.download(f"/verifications/{args.verification_id}/evidence-report{suffix}")
        path = Path(args.file); path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
        return {"file": str(path), "bytes": len(data), "format": "pdf" if args.pdf else "archive"}
    bases = {"projects": "/projects/", "api-clients": "/api-clients/", "workflows": "/workflows/", "templates": "/workflow-templates/", "webhooks": "/webhook-endpoints/"}
    base = bases[command]
    id_attr = {"projects": "project_id", "api-clients": "api_client_id", "workflows": "workflow_id", "templates": "template_id", "webhooks": "webhook_id"}.get(command)
    identifier = quote(str(getattr(args, id_attr, "")), safe="") if id_attr else ""
    if action == "list":
        extra = {}
        for key in ("environment", "project_id", "category", "search"):
            if hasattr(args, key): extra[key] = getattr(args, key)
        return client.request("GET", base + _query(cursor=getattr(args, "cursor", ""), limit=getattr(args, "limit", None), page=getattr(args, "page", None), page_size=getattr(args, "page_size", None), status=getattr(args, "status", ""), **extra))
    if action == "get": return client.request("GET", base + identifier)
    if action == "create":
        if command == "projects": body = {"name": args.name, "environment": args.environment, "description": args.description}
        elif command == "api-clients": body = {"name": args.name, "project_id": args.project_id, "scopes": args.scopes, "allowed_networks": args.allowed_network}
        elif command == "workflows": body = {**_json_object(args.definition, "--definition"), "name": args.name, "project_id": args.project_id}
        else: body = {"url": args.url, "events": args.event, "project_id": args.project_id, "description": args.description}
        return client.request("POST", base, body)
    if command == "workflows" and action == "versions": return client.request("GET", f"{base}{identifier}/versions")
    if command == "webhooks" and action == "test": return client.request("POST", f"{base}{identifier}/test", {"event": args.event, "payload": _json_object(args.payload, "--payload")})
    return client.request("POST", f"{base}{identifier}/{action}", {})


def _handle_profiles(args: argparse.Namespace) -> Any:
    config = _load_config()
    profiles = config.get("profiles", {}) if isinstance(config.get("profiles"), dict) else {}
    action = args.profiles_command
    if action == "list":
        return {"current": args.profile, "results": [{"name": name, "environment": value.get("environment", "custom"), "api_origin": value.get("api_origin", "")} for name, value in sorted(profiles.items())]}
    if action == "current":
        current = _profile(config, args.profile)
        visible = {key: value for key, value in current.items() if key not in {"client_secret", "access_token"}}
        return {"name": args.profile, **visible, "authenticated": bool(current.get("client_secret") or current.get("access_token"))}
    if args.name not in profiles:
        raise IdentityCoreError(f"Profile '{args.name}' does not exist.")
    del profiles[args.name]; config["profiles"] = profiles; _save_config(config)
    return {"deleted": args.name}


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "completion":
        print(_completion_script(args.shell)); return 0
    try:
        if args.command == "login":
            if not args.api_origin and not args.environment:
                raise IdentityCoreError("--api-origin or --environment is required.")
            secret = args.client_secret
            token = args.access_token
            if not token and not secret and sys.stdin.isatty():
                secret = getpass.getpass("IdentityCore client secret: ")
            if not token and (not args.client_id or not secret):
                raise IdentityCoreError("--access-token or --client-id and --client-secret are required (environment variables are recommended in CI).")
            config = _load_config(); profiles = config.get("profiles", {}) if isinstance(config.get("profiles"), dict) else {}
            profiles[args.profile] = {"environment": args.environment or "custom", "api_origin": args.api_origin or ENVIRONMENTS[args.environment], "client_id": args.client_id or "", "client_secret": secret or "", "access_token": token or ""}
            config = {"profiles": profiles}; _save_config(config)
            _print({"profile": args.profile, "configuration": str(_config_path())}, args.output); return 0
        if args.command == "profiles":
            _print(_handle_profiles(args), args.output); return 0
        _print(_dispatch(_client(args), args), args.output); return 0
    except IdentityCoreError as exc:
        error: dict[str, Any] = {"error": {"type": exc.__class__.__name__, "message": str(exc)}}
        if isinstance(exc, IdentityCoreAPIError):
            error["error"].update({"code": exc.code, "status": exc.status, "request_id": exc.request_id, "details": exc.details})
        print(json.dumps(error, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
