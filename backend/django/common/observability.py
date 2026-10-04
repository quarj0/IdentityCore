"""Django/Celery boundaries for the shared, payload-free telemetry contract."""

# common.safe_logging makes backend/shared importable in Django deployments.
from common import safe_logging  # noqa: F401

from shared.observability import (
    ENVIRONMENT,
    configure,
    environment,
    inject,
    metrics,
    observed,
    record_completion,
)  # noqa: F401
from shared import observability as telemetry
from celery import signals
import time


def set_verification_environment(verification):
    project = verification.project
    telemetry.ENVIRONMENT.set(
        telemetry.environment(project.environment if project else "sandbox")
    )


class ObservabilityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from common.responses import get_request_id

        token = telemetry.ENVIRONMENT.set("unknown")
        try:
            with telemetry.operation(
                "api", "request", context=telemetry.extract(request.headers)
            ) as span:
                request._request_id = get_request_id(request)
                response = self.get_response(request)
                telemetry.record_response("api", response.status_code >= 500)
                if response.status_code >= 500:
                    span.set_status(telemetry.Status(telemetry.StatusCode.ERROR))
                response["X-Request-Id"] = request._request_id
                # The random trace ID correlates support without exporting request IDs.
                response["X-Trace-Id"] = format(
                    span.get_span_context().trace_id, "032x"
                )
                return response
        finally:
            telemetry.ENVIRONMENT.reset(token)


@signals.before_task_publish.connect(weak=False)
def before_publish(sender=None, headers=None, **kwargs):
    if headers is not None:
        telemetry.inject(headers)
        headers["identitycore_environment"] = telemetry.environment(
            telemetry.ENVIRONMENT.get()
        )
        headers["identitycore_enqueued_at"] = time.time()


@signals.task_prerun.connect(weak=False)
def before_task(sender=None, **kwargs):
    request = sender.request
    headers = request.headers or {}
    # Store tokens on this invocation, never globally: concurrent tasks are isolated.
    request._telemetry_environment = telemetry.ENVIRONMENT.set(
        telemetry.environment(headers.get("identitycore_environment"))
    )
    boundary = telemetry.operation("worker", "task", context=telemetry.extract(headers))
    request._telemetry_boundary = boundary
    boundary.__enter__()
    try:
        delay = max(0, time.time() - float(headers["identitycore_enqueued_at"]))
    except (KeyError, ValueError, TypeError):
        return
    if delay < 86400 * 30:
        telemetry.metrics.get_meter("identitycore").create_histogram(
            "identitycore.queue.wait", unit="s"
        ).record(
            delay, {"environment": telemetry.environment(telemetry.ENVIRONMENT.get())}
        )


@signals.task_postrun.connect(weak=False)
def after_task(sender=None, state=None, **kwargs):
    request = sender.request
    boundary = getattr(request, "_telemetry_boundary", None)
    if boundary is not None:
        if state in {"FAILURE", "REVOKED"}:
            failure = RuntimeError("worker task failed")
            boundary.__exit__(RuntimeError, failure, None)
        else:
            boundary.__exit__(None, None, None)
        telemetry.ENVIRONMENT.reset(request._telemetry_environment)
