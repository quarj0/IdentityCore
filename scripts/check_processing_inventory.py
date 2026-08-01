#!/usr/bin/env python3
"""Validate the repository records-of-processing inventory."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "docs/privacy/processing-inventory.json"
REQUIRED = {"id", "fields", "purpose", "locations", "retention", "processors", "transfers", "owners"}


def main() -> int:
    data = json.loads(INVENTORY.read_text(encoding="utf-8"))
    owners = data.get("owners", {})
    activities = data.get("activities", [])
    ids: set[str] = set()
    errors: list[str] = []
    for activity in activities:
        activity_id = activity.get("id", "<missing id>")
        missing = REQUIRED - activity.keys()
        if missing:
            errors.append(f"{activity_id}: missing {', '.join(sorted(missing))}")
        if activity_id in ids:
            errors.append(f"{activity_id}: duplicate id")
        ids.add(activity_id)
        for key in REQUIRED - {"id"}:
            if key in activity and not activity[key]:
                errors.append(f"{activity_id}: {key} must not be empty")
        for owner in activity.get("owners", []):
            if owner not in owners:
                errors.append(f"{activity_id}: unknown owner {owner!r}")
        for location in activity.get("locations", []):
            if not (ROOT / location).exists():
                errors.append(f"{activity_id}: location does not exist: {location}")
    if not activities:
        errors.append("inventory contains no activities")
    if errors:
        raise SystemExit("processing inventory invalid:\n- " + "\n- ".join(errors))
    print(f"processing inventory valid: {len(activities)} activities, {len(owners)} owners")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
