import os
"""
Telemetry Configuration
OpenTelemetry and Traceloop instrumentation setup.
"""
import logging
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.starlette import StarletteInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from .config_loader import OTLP_ENDPOINT, DEPLOYMENT_ENV

logger = logging.getLogger(__name__)

def setup_telemetry(app, service_name: str, service_version: str = "1.0.0"):
    """
    Configures OpenTelemetry and Jaeger for the application.
    """
    logger.info(f"Configuring Telemetry for {service_name} (OTLP Endpoint: {OTLP_ENDPOINT})")
    
    resource = Resource(attributes={
        "service.name": service_name,
        "service.version": service_version,
        "deployment.environment": DEPLOYMENT_ENV
    })
    
    # Create and register TracerProvider
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)
    
    # Configure Jaeger Exporter (OTLP gRPC)
    try:
        otlp_exporter = OTLPSpanExporter(endpoint=OTLP_ENDPOINT, insecure=True)
        tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        logger.info(f"Telemetry enabled. Exporting to {OTLP_ENDPOINT}")
    except Exception as e:
        logger.error(f"Failed to initialize OTLP exporter: {e}")

    # Instrument the Starlette app
    StarletteInstrumentor().instrument_app(app)
