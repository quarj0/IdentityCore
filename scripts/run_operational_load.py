#!/usr/bin/env python3
"""Production-like orchestration load with isolated services and synthetic media.

Real HTTP/Gunicorn, PostgreSQL, Redis/Celery, S3 HTTP and signed webhooks; AI
uses explicit latency fixtures and real storage reads, never real applicants.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import io
import json
import math
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
from threading import Lock
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:18080/api/v1"


class LoadFailure(RuntimeError):
    """Fixed, payload-free failure code safe for a retained report."""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--rate-per-minute", type=float, default=30)
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--duration-seconds", type=int, default=60)
    parser.add_argument("--ai-latency-seconds", type=float, default=0.1)
    parser.add_argument("--telemetry", action="store_true")
    parser.add_argument("--poll-interval-seconds", type=float, default=3.5)
    parser.add_argument(
        "--poll-mode", choices=("session", "partner"), default="session"
    )
    parser.add_argument(
        "--profile-report",
        help="Optional payload-free function timing diagnostics; run separately from benchmarks",
    )
    parser.add_argument(
        "--burst",
        action="store_true",
        help="Start the configured concurrent applicant burst before steady arrivals",
    )
    args = parser.parse_args()
    if (
        args.rate_per_minute <= 0
        or args.concurrency < 1
        or args.duration_seconds < 1
        or args.poll_interval_seconds <= 0
    ):
        raise ValueError("Positive workload settings are required")
    values = dict(
        line.split("=", 1)
        for line in Path(args.env_file).read_text().splitlines()
        if line and not line.startswith("#")
    )
    env = dict(os.environ)
    env.update(
        {
            "DJANGO_SETTINGS_MODULE": "operational_load.settings",
            "DJANGO_SECRET_KEY": values["DRILL_APPLICATION_SECRET"],
            "DJANGO_ALLOWED_HOSTS": "127.0.0.1,localhost",
            "IDENTITYCORE_SYNTHETIC_LOAD": "1",
            "POSTGRES_DB": "identitycore_load",
            "POSTGRES_USER": values["POSTGRES_USER"],
            "POSTGRES_PASSWORD": values["POSTGRES_PASSWORD"],
            "POSTGRES_HOST": "127.0.0.1",
            "POSTGRES_PORT": "5444",
            "REDIS_URL": "redis://127.0.0.1:6388/4",
            "CELERY_BROKER_URL": "redis://127.0.0.1:6388/4",
            "CELERY_RESULT_BACKEND": "redis://127.0.0.1:6388/4",
            "OBJECT_STORAGE_PROVIDER": "s3_compatible",
            "OBJECT_STORAGE_ENDPOINT_URL": "http://127.0.0.1:9000",
            "OBJECT_STORAGE_ACCESS_KEY_ID": values["DRILL_STORAGE_ACCESS_KEY"],
            "OBJECT_STORAGE_SECRET_ACCESS_KEY": values["DRILL_STORAGE_SECRET_KEY"],
            "OBJECT_STORAGE_REGION": "us-east-1",
            "OBJECT_STORAGE_USE_PATH_STYLE": "1",
            "AI_SERVICE_BASE_URL": "http://127.0.0.1:18081",
            "AI_SERVICE_SHARED_TOKEN": values["DRILL_APPLICATION_SECRET"],
            "IDENTITYCORE_TELEMETRY_ENABLED": "1" if args.telemetry else "0",
            "OTEL_EXPORTER_OTLP_ENDPOINT": "http://127.0.0.1:4318",
            "IDENTITYCORE_SERVICE_NAME": "identitycore-api",
        }
    )
    env.pop("IDENTITYCORE_LOAD_PROFILE_FILE", None)
    if args.profile_report:
        env["IDENTITYCORE_LOAD_PROFILE_FILE"] = args.profile_report
    for role in ("MEDIA", "TEMP", "EVIDENCE", "PUBLIC"):
        env["OBJECT_STORAGE_" + role + "_BUCKET"] = "load-" + role.lower()
    env["PYTHONPATH"] = os.pathsep.join(
        [str(ROOT / "scripts"), str(ROOT / "backend/django"), str(ROOT / "backend")]
    )
    os.environ.update(env)
    sys.path[:0] = [
        str(ROOT / "scripts"),
        str(ROOT / "backend/django"),
        str(ROOT / "backend"),
    ]
    import psycopg
    import httpx
    import django
    from PIL import Image
    import redis
    import boto3
    from botocore.config import Config

    with psycopg.connect(
        host="127.0.0.1",
        port=5444,
        user=values["POSTGRES_USER"],
        password=values["POSTGRES_PASSWORD"],
        dbname="postgres",
        autocommit=True,
    ) as admin:
        if admin.execute(
            "SELECT 1 FROM pg_database WHERE datname='identitycore_load'"
        ).fetchone():
            raise RuntimeError(
                "Synthetic load database already exists; use a new dedicated target"
            )
        admin.execute("CREATE DATABASE identitycore_load")
    django.setup()
    import logging

    logging.getLogger("httpx").setLevel(logging.WARNING)
    from django.core.management import call_command
    from django.db import connection
    from apps.organizations.models import Organization
    from apps.tenants.models import Tenant
    from apps.accounts.models import PlatformUser
    from apps.projects.models import Project
    from apps.api_clients.models import APIClient
    from apps.access_control.models import Role, Permission, RolePermission, UserRole
    from apps.verification_policies.models import VerificationPolicy
    from apps.consent.models import ConsentTemplate
    from apps.webhooks.models import WebhookEndpoint, WebhookEvent
    from apps.webhooks.services import process_pending_webhook_events
    from apps.audit.services import verify_audit_chain
    from common.storage import get_object_bytes
    from apps.verifications.models import (
        ProcessingJob,
        VerificationDecision,
    )
    from rest_framework_simplejwt.tokens import RefreshToken
    from operational_load.fixtures import Fixtures

    call_command("migrate", verbosity=0, interactive=False)
    storage = boto3.client(
        "s3",
        endpoint_url=env["OBJECT_STORAGE_ENDPOINT_URL"],
        aws_access_key_id=values["DRILL_STORAGE_ACCESS_KEY"],
        aws_secret_access_key=values["DRILL_STORAGE_SECRET_KEY"],
        region_name="us-east-1",
        config=Config(s3={"addressing_style": "path"}),
    )
    for role in ("media", "temp", "evidence", "public"):
        storage.create_bucket(Bucket="load-" + role)
    redis.Redis.from_url(
        env["CELERY_BROKER_URL"]
    ).flushdb()  # Dedicated fixture DB 4 only.
    redis.Redis.from_url(
        "redis://127.0.0.1:6388/5"
    ).flushdb()  # Dedicated throttle fixture DB.
    tenants, webhook_secrets = [], {}
    for number in (1, 2):
        organization = Organization.objects.create(
            name=f"Synthetic load {number}", slug=f"load-{number}", status="active"
        )
        tenant = Tenant.objects.create(
            organization=organization,
            name=f"Synthetic load {number}",
            slug=f"load-{number}",
            status="active",
        )
        owner = PlatformUser.objects.create_user(
            email=f"synthetic-owner-{number}@example.invalid",
            password="SyntheticLoad123!",
            tenant=tenant,
            status="active",
        )
        reviewer = PlatformUser.objects.create_user(
            email=f"synthetic-reviewer-{number}@example.invalid",
            password="SyntheticLoad123!",
            tenant=tenant,
            status="active",
        )
        project = Project.objects.create(
            tenant=tenant,
            name="Production",
            slug="production",
            environment="production",
            created_by=owner,
        )
        role = Role.objects.create(
            tenant=tenant, name="Synthetic reviewer", scope="tenant"
        )
        permission, _ = Permission.objects.get_or_create(
            code="review_verification", defaults={"name": "Review verification"}
        )
        RolePermission.objects.create(role=role, permission=permission)
        UserRole.objects.create(user=reviewer, role=role, tenant=tenant)
        policy = VerificationPolicy.objects.create(
            tenant=tenant,
            project=project,
            name="Synthetic workflow",
            version=1,
            status="active",
            required_document_types_json=["national_id"],
            required_liveness_level="passive",
            face_match_threshold="0.85",
            manual_review_threshold="0.65",
            verification_expiry_minutes=60,
            media_retention_days=1,
            metadata_retention_days=1,
            created_by=owner,
        )
        ConsentTemplate.objects.create(
            tenant=tenant,
            name="Synthetic consent",
            version=1,
            language="en",
            content="Synthetic load-test consent",
            status="active",
            created_by=owner,
        )
        api = APIClient(
            tenant=tenant,
            project=project,
            name="Synthetic load",
            created_by=owner,
            scopes_json=["verifications:create", "verifications:read"],
            rate_limit_per_minute=10000,
        )
        api_raw_secret = APIClient.generate_client_secret()
        api.set_client_secret(api_raw_secret, generated=True)
        api.save()
        secret = uuid.uuid4().hex
        webhook_secrets[f"/webhooks/{number}"] = secret
        webhook = WebhookEndpoint(
            tenant=tenant,
            project=project,
            url=f"http://127.0.0.1:18081/webhooks/{number}",
            events_json=[
                "verification.verified",
                "verification.manual_review_required",
            ],
            created_by=owner,
        )
        webhook.set_secret(secret)
        webhook.save()
        tenants.append(
            {
                "api_headers": {
                    "X-Client-Id": api.client_id,
                    "Authorization": "Bearer " + api_raw_secret,
                },
                "review_headers": {
                    "Authorization": "Bearer "
                    + str(RefreshToken.for_user(reviewer).access_token)
                },
                "policy": policy.public_id,
            }
        )
    connection.close()
    random_bytes = random.Random(2026).randbytes(1280 * 960 * 3)
    buffer = io.BytesIO()
    Image.frombytes("RGB", (1280, 960), random_bytes).save(
        buffer, format="JPEG", quality=90
    )
    media = buffer.getvalue()
    lock = Lock()
    timings = {
        name: []
        for name in (
            "session",
            "upload",
            "document_processing",
            "biometric_processing",
            "review",
            "journey",
            "dispatch_wait",
        )
    }
    failures = []
    active = 0
    peak_active = 0
    # Retire idle connections before Gunicorn does; never retry/reset failed journeys.
    api = httpx.Client(timeout=30, limits=httpx.Limits(keepalive_expiry=1.0))
    process_logs = []
    processes = []
    fixtures = Fixtures(
        storage,
        env["AI_SERVICE_SHARED_TOKEN"],
        webhook_secrets,
        args.ai_latency_seconds,
    )
    fixtures.start()

    def measured(name, function):
        started = time.monotonic()
        result = function()
        with lock:
            timings[name].append(time.monotonic() - started)
        return result

    def request(method, path, headers, body=None):
        try:
            response = api.request(method, BASE + path, headers=headers, json=body)
        except httpx.HTTPError as error:
            raise LoadFailure(
                f"{type(error).__name__} at {method} {path.split('/')[1]}"
            ) from error
        if response.status_code not in (200, 201, 202):
            # Report only status and fixed route template; response bodies may
            # contain tokens or evidence and are excluded from load artifacts.
            raise LoadFailure(f"HTTP {response.status_code} at {path.split('/')[1]}")
        return response.json()["data"]

    def wait_status(verification_id, headers, expected, timeout=120):
        until = time.monotonic() + timeout
        while time.monotonic() < until:
            path = (
                "/sessions/" + verification_id + "/status"
                if args.poll_mode == "session"
                else "/verifications/" + verification_id
            )
            data = request("GET", path, headers)
            if data.get("status") in expected:
                return data
            time.sleep(args.poll_interval_seconds)
        raise LoadFailure("Synthetic processing deadline exceeded")

    def journey(number, scheduled):
        nonlocal active, peak_active
        with lock:
            active += 1
            peak_active = max(peak_active, active)
        tenant = tenants[number % len(tenants)]
        started = scheduled
        with lock:
            timings["dispatch_wait"].append(max(0, time.monotonic() - scheduled))
        try:
            headers = {
                **tenant["api_headers"],
                "Idempotency-Key": "synthetic-load-" + str(number),
            }
            created = measured(
                "session",
                lambda: request(
                    "POST",
                    "/verifications/",
                    headers,
                    {
                        "external_reference": "synthetic-" + str(number),
                        "purpose": "Synthetic operational load",
                        "policy_id": tenant["policy"],
                        "verification_subject": {"full_name": "Synthetic Applicant"},
                        "metadata": {
                            "country_code": "GH",
                            "document_type": "national_id",
                        },
                    },
                ),
            )
            verification_id = created["id"]
            session_id = created["session_id"]
            session_headers = {
                "Authorization": "Bearer " + created["session_token"],
                "X-Session-Id": session_id,
            }
            session = request("GET", "/sessions/" + session_id, session_headers)
            consent = session["consent"]
            request(
                "POST",
                f"/sessions/{session_id}/consent",
                session_headers,
                {
                    "accepted": True,
                    "template_id": consent["template_id"],
                    "version": consent["version"],
                    "locale": consent["locale"],
                    "content_hash": consent["content_hash"],
                },
            )

            def upload(purpose):
                uploaded = request(
                    "POST",
                    "/uploads/",
                    session_headers,
                    {
                        "purpose": purpose,
                        "mime_type": "image/jpeg",
                        "file_size_bytes": len(media),
                    },
                )
                response = api.put(
                    uploaded["upload_url"],
                    content=media,
                    headers=uploaded["upload_headers"],
                )
                if response.status_code != 200:
                    raise LoadFailure("Synthetic storage upload failed")
                request(
                    "POST",
                    f"/uploads/{uploaded['upload_id']}/complete",
                    session_headers,
                )
                return uploaded["upload_id"]

            front = measured("upload", lambda: upload("document_capture"))
            back = measured("upload", lambda: upload("document_capture"))
            request(
                "POST",
                f"/sessions/{session_id}/documents",
                session_headers,
                {
                    "document_type": "national_id",
                    "country_code": "GH",
                    "captures": [
                        {"side": "front", "upload_id": front},
                        {"side": "back", "upload_id": back},
                    ],
                },
            )
            measured(
                "document_processing",
                lambda: wait_status(
                    session_id if args.poll_mode == "session" else verification_id,
                    (
                        session_headers
                        if args.poll_mode == "session"
                        else tenant["api_headers"]
                    ),
                    {"awaiting_selfie"},
                ),
            )
            selfie = measured("upload", lambda: upload("selfie_capture"))
            captured = request(
                "POST",
                f"/sessions/{session_id}/selfies",
                session_headers,
                {"capture_type": "image", "upload_id": selfie},
            )
            request(
                "POST",
                f"/sessions/{session_id}/liveness",
                session_headers,
                {
                    "liveness_type": "passive",
                    "selfie_capture_id": captured["selfie_capture_id"],
                },
            )
            measured(
                "biometric_processing",
                lambda: wait_status(
                    session_id if args.poll_mode == "session" else verification_id,
                    (
                        session_headers
                        if args.poll_mode == "session"
                        else tenant["api_headers"]
                    ),
                    {"manual_review_required"},
                ),
            )
            review_headers = {
                **tenant["review_headers"],
                "Idempotency-Key": "synthetic-review-" + str(number),
            }
            measured(
                "review",
                lambda: request(
                    "POST",
                    f"/verifications/manual-reviews/{verification_id}/decision",
                    review_headers,
                    {
                        "decision": "verified",
                        "reason_code": "synthetic_review_confirmed",
                        "reason_detail": "Synthetic fixture reviewed",
                    },
                ),
            )
            final = request(
                "GET", "/verifications/" + verification_id, tenant["api_headers"]
            )
            if final.get("status") != "verified":
                raise LoadFailure("Synthetic human outcome did not persist")
            foreign = tenants[(number + 1) % len(tenants)]["api_headers"]
            denied = api.get(
                BASE + "/verifications/" + verification_id, headers=foreign
            )
            if denied.status_code not in (403, 404):
                raise LoadFailure("Synthetic tenant isolation check failed")
            with lock:
                timings["journey"].append(time.monotonic() - started)
            return verification_id
        except Exception as error:
            with lock:
                failures.append(
                    str(error)
                    if isinstance(error, LoadFailure)
                    else type(error).__name__
                )
            return None
        finally:
            with lock:
                active -= 1

    try:
        with tempfile.TemporaryDirectory(prefix="identitycore-load-") as logs:
            diagnostics_path = Path(logs) / "errors.jsonl"
            env["IDENTITYCORE_LOAD_DIAGNOSTICS_FILE"] = str(diagnostics_path)

            def start_process(name, command, process_env):
                output = open(Path(logs) / (name + ".log"), "w")
                process_logs.append(output)
                process = subprocess.Popen(
                    command,
                    cwd=ROOT / "backend/django",
                    env=process_env,
                    stdout=output,
                    stderr=subprocess.STDOUT,
                )
                processes.append(process)
                return process

            start_process(
                "api",
                [
                    sys.executable,
                    "-m",
                    "gunicorn",
                    "config.wsgi:application",
                    "--bind",
                    "127.0.0.1:18080",
                    "--workers",
                    "2",
                    "--threads",
                    "8",
                    "--keep-alive",
                    "2",
                ],
                env,
            )
            worker_env = {**env, "IDENTITYCORE_SERVICE_NAME": "identitycore-worker"}
            start_process(
                "worker",
                [
                    sys.executable,
                    "-m",
                    "celery",
                    "-A",
                    "config",
                    "worker",
                    "--pool=threads",
                    "--concurrency=4",
                    "--queues=ai_processing,webhooks",
                    "--loglevel=warning",
                ],
                worker_env,
            )
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline:
                try:
                    if api.get(BASE + "/health").status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(0.2)
            else:
                raise RuntimeError("Synthetic API startup failed")
            # Warm every API process through authenticated read routes. Capacity
            # is measured after readiness, separately from cold-start latency.
            warmed_workers = set()
            warmup_requests = 0

            def warm(number):
                response = api.get(
                    BASE + "/verifications/",
                    headers={
                        **tenants[number % len(tenants)]["api_headers"],
                        "Connection": "close",
                    },
                )
                if response.status_code != 200:
                    raise LoadFailure("Synthetic authenticated warmup failed")
                return response.headers.get("X-IdentityCore-Load-Worker")

            for _ in range(5):
                with ThreadPoolExecutor(max_workers=16) as warm_pool:
                    warmed_workers.update(warm_pool.map(warm, range(16)))
                warmup_requests += 16
                if len(warmed_workers - {None}) == 2:
                    break
            else:
                raise LoadFailure("Synthetic worker readiness did not converge")
            steady_count = max(
                1, math.ceil(args.rate_per_minute * args.duration_seconds / 60)
            )
            burst_count = args.concurrency if args.burst else 0
            count = steady_count + burst_count
            run_started = time.monotonic()
            with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
                burst_started = time.monotonic()
                burst_futures = [
                    pool.submit(journey, number, burst_started)
                    for number in range(burst_count)
                ]
                completed_burst = [future.result() for future in burst_futures]
                burst_elapsed = time.monotonic() - burst_started
                steady_started = time.monotonic()
                futures = []
                for offset in range(steady_count):
                    number = burst_count + offset
                    scheduled = steady_started + offset * 60 / args.rate_per_minute
                    while time.monotonic() < scheduled:
                        time.sleep(min(0.1, scheduled - time.monotonic()))
                    futures.append(pool.submit(journey, number, scheduled))
                completed_steady = [future.result() for future in futures]
                completed = completed_burst + completed_steady
                steady_elapsed = max(
                    args.duration_seconds, time.monotonic() - steady_started
                )
            offered_window = max(args.duration_seconds, time.monotonic() - run_started)
            # Exercise the real signed HTTP transport and durable outbox, including
            # pending work that was not individually dispatched by producers.
            process_pending_webhook_events(limit=100000)
            drain_until = time.monotonic() + 60
            while (
                WebhookEvent.objects.filter(status="pending").exists()
                and time.monotonic() < drain_until
            ):
                process_pending_webhook_events(limit=100000)
                time.sleep(0.2)

            def summary(values):
                ordered = sorted(values)
                return (
                    {
                        "count": len(values),
                        "p95_seconds": round(
                            ordered[
                                min(
                                    len(ordered) - 1, math.ceil(len(ordered) * 0.95) - 1
                                )
                            ],
                            3,
                        ),
                        "max_seconds": round(max(ordered), 3),
                    }
                    if ordered
                    else {"count": 0, "p95_seconds": None, "max_seconds": None}
                )

            def evidence_reports_valid():
                from apps.verifications.models import Verification

                try:
                    for verification in Verification.objects.all():
                        metadata = verification.metadata_json or {}
                        json_key = metadata.get("evidence_report_storage_key")
                        pdf_key = metadata.get("evidence_report_pdf_storage_key")
                        if not json_key or not pdf_key:
                            return False
                        content, _ = get_object_bytes(
                            bucket_name="load-evidence",
                            key=json_key,
                            decrypt=metadata.get("evidence_report_encrypted", False),
                            encryption_purpose="evidence.reports",
                            tenant_scope=verification.tenant.public_id,
                            environment=(
                                verification.project.environment
                                if verification.project_id
                                else "sandbox"
                            ),
                        )
                        payload = json.loads(content)
                        if (
                            payload.get("verification_id") != verification.public_id
                            or payload.get("status") != "verified"
                            or payload.get("decision", {}).get("decision_type")
                            != "manual"
                            or payload.get("decision", {}).get("decision") != "verified"
                        ):
                            return False
                        if (
                            storage.head_object(Bucket="load-evidence", Key=pdf_key)[
                                "ContentLength"
                            ]
                            <= 0
                        ):
                            return False
                except Exception:
                    return False
                return True

            summaries = {name: summary(samples) for name, samples in timings.items()}
            thresholds = {
                "session": 2,
                "upload": 5,
                "document_processing": 30,
                "biometric_processing": 30,
                "review": 2,
                "journey": 60,
                "dispatch_wait": 2,
            }
            checks = {
                name: bool(summaries[name]["count"])
                and summaries[name]["p95_seconds"] <= limit
                for name, limit in thresholds.items()
            }
            checks.update(
                {
                    "audit_chains_valid": all(
                        verify_audit_chain(tenant_id=tenant.pk)[0]
                        for tenant in Tenant.objects.all()
                    ),
                    "evidence_reports_published": evidence_reports_valid(),
                    "zero_journey_failures": not failures,
                    "concurrent_burst_exercised": not args.burst
                    or peak_active == args.concurrency,
                    "all_offered_work_completed": sum(
                        item is not None for item in completed
                    )
                    == count,
                    "no_exhausted_jobs": not ProcessingJob.objects.filter(
                        status="exhausted"
                    ).exists(),
                    "no_processing_backlog": not ProcessingJob.objects.exclude(
                        status="completed"
                    ).exists(),
                    "all_webhooks_delivered": not WebhookEvent.objects.exclude(
                        status="delivered"
                    ).exists(),
                    "fixture_transport_errors": fixtures.errors == 0,
                    "review_decisions_preserved": VerificationDecision.objects.filter(
                        decision_type="manual", decision="verified"
                    ).count()
                    == count,
                }
            )
            report = {
                "date": time.strftime("%Y-%m-%d", time.gmtime()),
                "service_events": {
                    name: sum(
                        Path(logs, "api.log").read_text().count(marker)
                        for marker in markers
                    )
                    for name, markers in {
                        "worker_timeout": ["WORKER TIMEOUT"],
                        "worker_killed": ["was sent SIGKILL", "Worker exited"],
                        "listen_failure": ["Connection in use", "Can't connect"],
                    }.items()
                },
                "exception_evidence": (
                    [
                        json.loads(line)
                        for line in diagnostics_path.read_text().splitlines()
                    ]
                    if diagnostics_path.exists()
                    else []
                ),
                "scope": "isolated orchestration load; real HTTP/PostgreSQL/Redis/Celery and S3 HTTP fixture; synthetic AI latency",
                "target": {
                    "verifications_per_minute": args.rate_per_minute,
                    "concurrent_applicants": args.concurrency,
                    "duration_seconds": args.duration_seconds,
                    "status": "provisional pilot baseline",
                },
                "services": {
                    "gunicorn_workers": 2,
                    "gunicorn_threads_per_worker": 8,
                    "gunicorn_keepalive_seconds": 2,
                    "http_client_keepalive_seconds": 1.0,
                    "celery_threads": 4,
                    "cpu_count": os.cpu_count(),
                    "cpu_quota": (
                        Path("/sys/fs/cgroup/cpu.max").read_text().strip()
                        if Path("/sys/fs/cgroup/cpu.max").exists()
                        else "unavailable"
                    ),
                    "synthetic_ai_latency_seconds": args.ai_latency_seconds,
                    "telemetry_enabled": args.telemetry,
                    "profiling_enabled": bool(args.profile_report),
                    "poll_mode": args.poll_mode,
                    "poll_interval_seconds": args.poll_interval_seconds,
                },
                "media_bytes_per_upload": len(media),
                "warmup": {
                    "authenticated_read_requests": warmup_requests,
                    "api_processes_ready": len(warmed_workers),
                },
                "offered": count,
                "burst_offered": burst_count,
                "steady_offered": steady_count,
                "peak_active_applicants": peak_active,
                "phases": {
                    "burst_seconds": round(burst_elapsed, 3),
                    "steady_seconds": round(steady_elapsed, 3),
                    "steady_completed": sum(
                        item is not None for item in completed_steady
                    ),
                    "steady_completed_per_minute_including_tail": round(
                        sum(item is not None for item in completed_steady)
                        * 60
                        / steady_elapsed,
                        3,
                    ),
                },
                "completed": sum(item is not None for item in completed),
                "elapsed_seconds": round(offered_window, 3),
                "completed_per_minute": round(
                    sum(item is not None for item in completed) * 60 / offered_window, 3
                ),
                "latency": summaries,
                "thresholds_seconds": thresholds,
                "checks": checks,
                "failure_counts": {
                    reason: failures.count(reason) for reason in set(failures)
                },
                "webhook_deliveries": len(fixtures.events),
                "pass": all(checks.values()),
                "limitations": [
                    "S3 fixture does not benchmark production IAM or storage service limits",
                    "AI fixture measures configured latency and storage reads, not model inference capacity",
                    "Hardware/provider/quota target requires deployment-specific readiness approval",
                ],
            }
            Path(args.report).write_text(json.dumps(report, indent=2) + "\n")
            print(
                json.dumps(
                    {
                        "load_gate": "pass" if report["pass"] else "fail",
                        "completed": report["completed"],
                        "offered": count,
                        "failed_checks": [
                            name for name, passed in checks.items() if not passed
                        ],
                        "failure_counts": report["failure_counts"],
                    }
                )
            )
            if not report["pass"]:
                raise SystemExit(1)
    finally:
        for process in processes:
            process.terminate()
        for process in processes:
            try:
                process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        for output in process_logs:
            output.close()
        fixtures.stop()
        api.close()


if __name__ == "__main__":
    main()
