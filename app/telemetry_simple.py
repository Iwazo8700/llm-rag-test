"""
Simplified OpenTelemetry instrumentation for the RAG application.
"""

import asyncio
import functools
import logging
import os
import time
from typing import Any, Optional

from opentelemetry import metrics, trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.trace import Status, StatusCode

logger = logging.getLogger(__name__)


class TelemetryConfig:
    """Configuration for OpenTelemetry setup."""

    def __init__(self):
        self.service_name = os.getenv("OTEL_SERVICE_NAME", "rag-system")
        self.service_version = os.getenv("OTEL_SERVICE_VERSION", "1.0.0")
        self.environment = os.getenv("OTEL_ENVIRONMENT", "development")

        self.jaeger_endpoint = os.getenv(
            "JAEGER_ENDPOINT", "http://localhost:14268/api/traces"
        )

        self.console_export = os.getenv("OTEL_CONSOLE_EXPORT", "true").lower() == "true"


def setup_telemetry(config: Optional[TelemetryConfig] = None) -> None:
    """
    Set up OpenTelemetry tracing and metrics.

    Args:
        config: Telemetry configuration. If None, uses default config.
    """
    if not config:
        config = TelemetryConfig()

    resource = Resource.create(
        {
            "service.name": config.service_name,
            "service.version": config.service_version,
            "deployment.environment": config.environment,
        }
    )

    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    meter_provider = MeterProvider(resource=resource)
    metrics.set_meter_provider(meter_provider)

    logger.info(f"OpenTelemetry initialized for service: {config.service_name}")


def get_tracer(name: str = __name__):
    """Get a tracer instance."""
    return trace.get_tracer(name)


def get_meter(name: str = __name__):
    """Get a meter instance."""
    return metrics.get_meter(name)


def trace_function(operation_name: str, component: str = "app"):
    """Decorator to automatically trace function calls."""

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_as_current_span(operation_name) as span:
                set_span_attribute("component", component)
                set_span_attribute("function", func.__name__)

                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    set_span_attribute("success", True)
                    return result
                except Exception as e:
                    set_span_attribute("success", False)
                    set_span_attribute("error", str(e))
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise
                finally:
                    duration = time.time() - start_time
                    set_span_attribute("duration", duration)

                    # Record metrics
                    counter = metrics_collector.get_counter(
                        f"{component}_operations", f"{component.title()} operations"
                    )
                    counter.add(
                        1, {"operation": operation_name, "function": func.__name__}
                    )

                    histogram = metrics_collector.get_histogram(
                        f"{component}_duration",
                        f"{component.title()} operation duration",
                    )
                    histogram.record(
                        duration,
                        {"operation": operation_name, "function": func.__name__},
                    )

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_as_current_span(operation_name) as span:
                set_span_attribute("component", component)
                set_span_attribute("function", func.__name__)

                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    set_span_attribute("success", True)
                    return result
                except Exception as e:
                    set_span_attribute("success", False)
                    set_span_attribute("error", str(e))
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise
                finally:
                    duration = time.time() - start_time
                    set_span_attribute("duration", duration)

                    # Record metrics
                    counter = metrics_collector.get_counter(
                        f"{component}_operations", f"{component.title()} operations"
                    )
                    counter.add(
                        1, {"operation": operation_name, "function": func.__name__}
                    )

                    histogram = metrics_collector.get_histogram(
                        f"{component}_duration",
                        f"{component.title()} operation duration",
                    )
                    histogram.record(
                        duration,
                        {"operation": operation_name, "function": func.__name__},
                    )

        # Return the appropriate wrapper based on whether the function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def traced_operation(operation_name: str, **attributes):
    """
    Decorator for methods that need custom tracing with specific attributes.

    Args:
        operation_name: Name of the operation for tracing
        **attributes: Static attributes to add to the span

    Usage:
        @traced_operation("chromadb_add_document", component="database")
        def add_document(self, text, embedding, metadata=None):
            # Method implementation
            # Dynamic attributes can be added via set_span_attribute()
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()

            with tracer.start_as_current_span(operation_name) as span:
                for key, value in attributes.items():
                    span.set_attribute(key, str(value))

                span.set_attribute("function.name", func.__name__)

                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("operation.result", "success")
                    return result
                except Exception as e:
                    span.set_attribute("operation.result", "error")
                    span.set_attribute("operation.error", str(e))
                    span.record_exception(e)
                    raise

        return wrapper

    return decorator


def set_span_attribute(key: str, value: Any) -> None:
    """
    Set an attribute on the current active span.

    Args:
        key: Attribute key
        value: Attribute value
    """
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.set_attribute(key, str(value))


class TracedOperation:
    """Context manager for manual tracing operations."""

    def __init__(self, operation_name: str, attributes: Optional[dict] = None):
        self.operation_name = operation_name
        self.attributes = attributes or {}
        self.tracer = get_tracer()
        self.span = None

    def __enter__(self):
        self.span = self.tracer.start_span(self.operation_name)
        for key, value in self.attributes.items():
            self.span.set_attribute(key, str(value))
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.span.set_attribute("error", True)
            self.span.set_attribute("error.type", exc_type.__name__)
            self.span.set_attribute("error.message", str(exc_val))
            self.span.record_exception(exc_val)

        self.span.end()


class MetricsCollector:
    """Helper class for collecting custom metrics."""

    def __init__(self):
        self.meter = get_meter()
        self._counters = {}
        self._histograms = {}

    def get_counter(self, name: str, description: str = ""):
        """Get or create a counter metric."""
        if name not in self._counters:
            self._counters[name] = self.meter.create_counter(
                name=name,
                description=description,
            )
        return self._counters[name]

    def get_histogram(self, name: str, description: str = ""):
        """Get or create a histogram metric."""
        if name not in self._histograms:
            self._histograms[name] = self.meter.create_histogram(
                name=name,
                description=description,
            )
        return self._histograms[name]


metrics_collector = MetricsCollector()


def instrument_fastapi(app):
    """
    Instrument a FastAPI application with OpenTelemetry.

    Args:
        app: FastAPI application instance
    """
    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumentation enabled")
    except ImportError:
        logger.warning("FastAPI instrumentation not available")


def instrument_requests():
    """Enable automatic instrumentation for requests library."""
    try:
        RequestsInstrumentor().instrument()
        logger.info("Requests instrumentation enabled")
    except ImportError:
        logger.warning("Requests instrumentation not available")


def instrument_logging():
    """Enable automatic instrumentation for logging."""
    try:
        LoggingInstrumentor().instrument()
        logger.info("Logging instrumentation enabled")
    except ImportError:
        logger.warning("Logging instrumentation not available")


setup_telemetry()
