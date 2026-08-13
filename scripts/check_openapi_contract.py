#!/usr/bin/env python3
"""Fail when Django's supported public routes and OpenAPI diverge."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DJANGO_ROOT = ROOT / "backend" / "django"
sys.path.insert(0, str(DJANGO_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.testing")

import django  # noqa: E402

django.setup()

from config.api_views import OPENAPI_SPEC_PATH  # noqa: E402
from config.openapi_contract import (  # noqa: E402
    load_contract,
    registered_public_operations,
    validate_contract,
)


def main() -> int:
    contract = load_contract(OPENAPI_SPEC_PATH)
    operations = registered_public_operations()
    validate_contract(contract, implemented_operations=operations)
    print(f"Validated {len(operations)} public OpenAPI operations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
