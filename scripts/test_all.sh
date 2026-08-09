#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CURRENT_SUITE="startup"

report_failure() {
  local exit_code=$?
  printf '\n[FAIL] %s test suite failed (exit code %d).\n' "$CURRENT_SUITE" "$exit_code" >&2
  exit "$exit_code"
}

trap report_failure ERR

run_suite() {
  CURRENT_SUITE="$1"
  shift
  printf '\n==> Running %s tests\n' "$CURRENT_SUITE"
  "$@"
  printf '[PASS] %s tests\n' "$CURRENT_SUITE"
}

cd "$ROOT_DIR"

run_suite "generated SDK model drift" uv run --project backend python scripts/generate_sdk_models.py --check

run_suite "Django backend" env DJANGO_SETTINGS_MODULE=config.settings.testing \
  uv run --project backend python backend/django/manage.py test apps common config
run_suite "AI service" uv run --project backend pytest backend/ai-service/tests
run_suite "frontend unit" pnpm --dir frontend --recursive --if-present test
run_suite "verification portal end-to-end" \
  pnpm --dir frontend --filter verification-portal test:e2e
run_suite "Python SDK" python -m unittest discover -s sdk/python/tests
run_suite "JavaScript SDK" npm --prefix sdk/javascript test
run_suite "Java SDK" mvn --batch-mode -f sdk/java/pom.xml test
run_suite ".NET SDK" dotnet test sdk/dotnet/IdentityCore.sln --configuration Release

printf '\nAll test suites passed.\n'
