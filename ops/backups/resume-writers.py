#!/usr/bin/env python3
"""Systemd stop recovery independent of Django/database startup readiness."""

import json
import os
import subprocess

try:
    command = json.loads(os.environ["BACKUP_RESUME_COMMAND"])
    if (
        not command
        or not isinstance(command, list)
        or any(not isinstance(arg, str) for arg in command)
    ):
        raise ValueError("Invalid resume argv")
    subprocess.run(
        command,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=300,
    )
except Exception:
    raise SystemExit(
        "Backup writer resume failed; inspect restricted infrastructure diagnostics."
    ) from None
