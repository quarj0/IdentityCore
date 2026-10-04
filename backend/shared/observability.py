"""Payload-free telemetry shared by API, workers and AI.

Only fixed operation names and enumerated dimensions are exported. In particular,
SDK exception recording is disabled: exception messages may contain evidence.
"""

from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
import os
import logging
import threading
import time
import uuid

from opentelemetry import metrics, trace
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.trace import Status, StatusCode

ENVIRONMENT = ContextVar("telemetry_environment", default="unknown")
PROPAGATOR = TraceContextTextMapPropagator()  # Never propagate baggage.
_lock = threading.Lock()
_initialized = False
_correlation_installed = False
_process_pid = None
_process_instance = None
OPERATIONS = frozenset(
    {"api", "ai", "provider", "storage", "webhook", "worker", "verification"}
)


def configure(service: str) -> None:
    """Optional OTLP export; a collector outage never blocks processing."""
    global _initialized
    install_log_correlation()
    if _initialized or os.getenv("IDENTITYCORE_TELEMETRY_ENABLED", "0") != "1":
        return
    with _lock:
        if _initialized:
            return
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased
        from opentelemetry.sdk.metrics import MeterProvider, Histogram
        from opentelemetry.sdk.metrics.view import (
            View,
            ExplicitBucketHistogramAggregation,
        )
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
            OTLPMetricExporter,
        )

        resource = Resource(
            {"service.name": service, "service.instance.id": process_instance()}
        )
        provider = TracerProvider(
            resource=resource,
            sampler=ParentBased(
                TraceIdRatioBased(
                    float(os.getenv("IDENTITYCORE_TRACE_SAMPLE_RATIO", "0.1"))
                )
            ),
        )
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(timeout=5)))
        trace.set_tracer_provider(provider)
        metrics.set_meter_provider(
            MeterProvider(
                resource=resource,
                views=[
                    View(
                        instrument_type=Histogram,
                        aggregation=ExplicitBucketHistogramAggregation(
                            boundaries=(
                                0.01,
                                0.05,
                                0.1,
                                0.25,
                                0.5,
                                1,
                                2,
                                5,
                                10,
                                30,
                                60,
                                120,
                                300,
                                600,
                            )
                        ),
                    )
                ],
                metric_readers=[
                    PeriodicExportingMetricReader(
                        OTLPMetricExporter(timeout=5), export_interval_millis=15000
                    )
                ],
            )
        )
        _initialized = True


def environment(value):
    return value if value in {"sandbox", "production"} else "unknown"


def inject(headers):
    PROPAGATOR.inject(headers)


def extract(headers):
    # Vendor tracestate is free-form and may contain identifiers. Preserve only
    # the fixed W3C traceparent fields; discard tracestate and baggage.
    return PROPAGATOR.extract({"traceparent": headers.get("traceparent", "")})


@contextmanager
def operation(component, name, *, context=None, environment_name=None):
    if (
        component not in OPERATIONS
        or not name.replace("_", "").replace(".", "").isalnum()
    ):
        raise ValueError("Telemetry operation names must be fixed code constants.")
    attributes = {
        "component": component,
        "operation": name,
        "environment": environment(environment_name or ENVIRONMENT.get()),
    }
    started = time.monotonic()
    outcome = "success"
    tracer = trace.get_tracer("identitycore")
    with tracer.start_as_current_span(
        f"{component}.{name}",
        context=context,
        attributes=attributes,
        record_exception=False,
        set_status_on_exception=False,
    ) as span:
        try:
            yield span
        except BaseException:
            outcome = "error"
            span.set_status(Status(StatusCode.ERROR))
            raise
        finally:
            attributes["environment"] = environment(
                environment_name or ENVIRONMENT.get()
            )
            span.set_attribute("environment", attributes["environment"])
            attributes["process_instance"] = process_instance()
            attributes["outcome"] = outcome
            meter = metrics.get_meter("identitycore")
            meter.create_counter("identitycore.operations", unit="1").add(1, attributes)
            meter.create_histogram("identitycore.operation.duration", unit="s").record(
                time.monotonic() - started, attributes
            )


def observed(component, name):
    def decorate(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            with operation(component, name):
                return function(*args, **kwargs)

        return wrapped

    return decorate


def record_response(component, failed):
    metrics.get_meter("identitycore").create_counter(
        "identitycore.responses", unit="1"
    ).add(
        1,
        {
            "component": component,
            "process_instance": process_instance(),
            "environment": environment(ENVIRONMENT.get()),
            "outcome": "error" if failed else "success",
        },
    )


def record_completion(failed, duration, environment_name):
    attributes = {
        "environment": environment(environment_name),
        "process_instance": process_instance(),
        "outcome": "error" if failed else "success",
    }
    meter = metrics.get_meter("identitycore")
    meter.create_counter("identitycore.processing.completed", unit="1").add(
        1, attributes
    )
    meter.create_histogram("identitycore.processing.duration", unit="s").record(
        duration, attributes
    )


def install_log_correlation():
    global _correlation_installed
    if not _correlation_installed:
        original_factory = logging.getLogRecordFactory()

        def correlated_record(*args, **kwargs):
            record = original_factory(*args, **kwargs)
            span = trace.get_current_span().get_span_context()
            record.ic_trace_id = format(span.trace_id, "032x") if span.is_valid else "-"
            record.ic_span_id = format(span.span_id, "016x") if span.is_valid else "-"
            return record

        logging.setLogRecordFactory(correlated_record)
        _correlation_installed = True


def process_instance():
    """Bounded deployment cardinality; distinguish forked Celery/Gunicorn counters."""
    global _process_pid, _process_instance
    if _process_pid != os.getpid():
        _process_pid = os.getpid()
        _process_instance = uuid.uuid4().hex
    return _process_instance
