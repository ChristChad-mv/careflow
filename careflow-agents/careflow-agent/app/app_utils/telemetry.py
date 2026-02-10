import os
import logging
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from .config_loader import OTLP_ENDPOINT, DEPLOYMENT_ENV

logger = logging.getLogger(__name__)

def setup_telemetry(app, service_name: str, service_version: str = "1.0.0"):
    """
    Configures Telemetry for the application.
    Prioritizes Cloud Trace if available, otherwise falls back to OTLP or logs.
    """
    logger.info(f"🛰️ Configuring Telemetry for {service_name}")
    
    resource = Resource(attributes={
        "service.name": service_name,
        "service.version": service_version,
        "deployment.environment": DEPLOYMENT_ENV
    })
    
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)
    
    # --- 1. Exporters Setup ---
    try:
        from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
        logger.info("☁️ Enabling Google Cloud Trace exporter...")
        cloud_exporter = CloudTraceSpanExporter()
        tracer_provider.add_span_processor(BatchSpanProcessor(cloud_exporter))
        logger.info("✅ Cloud Trace telemetry active.")
    except Exception as e:
        logger.warning(f"⚠️ Cloud Trace not available: {e}. Falling back to OTLP check.")
        
        # Fallback to OTLP only if specifically configured
        if "localhost" not in OTLP_ENDPOINT or os.environ.get("FORCE_OTLP"):
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
                otlp_exporter = OTLPSpanExporter(endpoint=OTLP_ENDPOINT, insecure=True)
                tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
                logger.info(f"✅ OTLP Telemetry enabled (Endpoint: {OTLP_ENDPOINT})")
            except Exception as otlp_e:
                logger.error(f"❌ Failed to initialize OTLP exporter: {otlp_e}")
        else:
            logger.info("🚫 Local OTLP collector skipped to avoid connection errors.")

    # --- 2. Instrumentations ---
    # We do these one by one inside try-except to be as resilient as possible
    
    # 2a. Starlette/FastAPI
    try:
        from opentelemetry.instrumentation.starlette import StarletteInstrumentor
        StarletteInstrumentor().instrument_app(app)
        logger.info("✅ Starlette instrumentation active.")
    except Exception as e:
        logger.warning(f"⚠️ Starlette instrumentation failed: {e}")

    # 2b. Aiohttp Client
    try:
        from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
        AioHttpClientInstrumentor().instrument()
        logger.info("✅ Aiohttp client instrumentation active.")
    except Exception as e:
        logger.debug(f"ℹ️ Aiohttp client instrumentation skipped or failed: {e}")

    # 2c. Requests
    try:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        RequestsInstrumentor().instrument()
        logger.info("✅ Requests instrumentation active.")
    except Exception as e:
        logger.debug(f"ℹ️ Requests instrumentation skipped or failed: {e}")

    # 2d. Google GenAI (Optional)
    try:
        from opentelemetry.instrumentation.google_genai import GoogleGenAiSdkInstrumentor
        GoogleGenAiSdkInstrumentor().instrument()
        logger.info("🎙️ GenAI SDK instrumentation enabled.")
    except Exception:
        pass
