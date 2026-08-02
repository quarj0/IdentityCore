#!/usr/bin/env bash
set -Eeuo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export DJANGO_SETTINGS_MODULE=config.settings.testing
rm -f "$root/backend/django/test.sqlite3"
server_pid=""

cleanup() {
  if [[ -n "$server_pid" ]]; then
    kill "$server_pid" 2>/dev/null || true
    wait "$server_pid" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

uv run --project "$root/backend" python "$root/backend/django/manage.py" migrate --noinput
fixture="$(uv run --project "$root/backend" python "$root/scripts/seed_sdk_compatibility.py")"
uv run --project "$root/backend" python "$root/backend/django/manage.py" runserver 127.0.0.1:8765 --noreload >"${RUNNER_TEMP:-/tmp}/identitycore-sdk-backend.log" 2>&1 &
server_pid=$!

for _ in {1..30}; do
  if curl --silent --fail http://127.0.0.1:8765/api/v1/health >/dev/null; then break; fi
  sleep 1
done
curl --silent --fail http://127.0.0.1:8765/api/v1/health >/dev/null

python - "$fixture" "${GITHUB_ENV:-/dev/stdout}" <<'PY'
import json, sys
values = json.loads(sys.argv[1])
lines = [
    "IDENTITYCORE_COMPAT_URL=http://127.0.0.1:8765",
    f"IDENTITYCORE_COMPAT_CLIENT_ID={values['client_id']}",
    f"IDENTITYCORE_COMPAT_CLIENT_SECRET={values['client_secret']}",
    f"IDENTITYCORE_COMPAT_POLICY_ID={values['policy_id']}",
]
with open(sys.argv[2], "a", encoding="utf-8") as output:
    output.write("\n".join(lines) + "\n")
PY
