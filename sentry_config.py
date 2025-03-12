import os
import sentry_sdk
from dotenv import load_dotenv
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.threading import ThreadingIntegration
from sentry_sdk.integrations.modules import ModulesIntegration
import logging

def get_integrations():
    """Get available Sentry integrations"""
    integrations = []

    # Always add these integrations
    integrations.extend(
        [
            ThreadingIntegration(),
            ModulesIntegration(),
            LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
        ]
    )

    # Try to add PostgreSQL integration
    try:
        from sentry_sdk.integrations.psycopg2 import Psycopg2Integration

        integrations.append(Psycopg2Integration())
    except Exception:
        print("Psycopg2 integration not available")

    # Try to add SQLAlchemy integration
    try:
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        integrations.append(SqlalchemyIntegration())
    except Exception:
        print("SQLAlchemy integration not available")

    return integrations

def init_sentry():
    """Initialize Sentry SDK with enhanced backend monitoring."""
    load_dotenv()

    # Get Sentry DSN from environment variable
    sentry_dsn = os.getenv("SENTRY_DSN")

    if not sentry_dsn:
        print(
            "Warning: SENTRY_DSN not found in environment variables. Sentry will not be initialized."
        )
        return

    # Set default tags using the SDK's set_tag method
    sentry_sdk.set_tag("component", "backend")
    sentry_sdk.set_tag("database", os.getenv("DB_NAME"))
    sentry_sdk.set_tag("host", os.getenv("DB_HOST"))

    # Initialize Sentry with enhanced performance monitoring
    sentry_sdk.init(
        dsn=sentry_dsn,
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "1.0")),
        profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "1.0")),
        environment=os.getenv("ENVIRONMENT", "development"),
        release="chess-game@1.0.0",
        integrations=get_integrations(),
        _experiments={
            "max_spans": 2000,  # Increased for better tracing
            "profiles_sample_rate": float(
                os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "1.0")
            ),
        },
        traces_sampler=traces_sampler,
        enable_tracing=True,
        # Performance monitoring settings
        send_default_pii=False,
        sample_rate=1.0,  # Capture all events for performance monitoring
        # Attach useful debugging information
        attach_stacktrace=True,
        max_breadcrumbs=100,  # Increased for better debugging
        # Set timeouts
        shutdown_timeout=5.0,  # Seconds to wait for data to be sent
    )

def traces_sampler(sampling_context):
    """Custom sampling function to control which transactions to capture."""
    # Get the transaction context
    ctx = sampling_context.get("transaction_context", {})
    op = ctx.get("op", "")
    name = ctx.get("name", "")

    # Always sample performance-critical operations
    if op in ["db", "http", "chess_move", "ai_move"]:
        return 1.0

    # Always sample critical operations
    if "create_" in name or "verify_" in name:
        return 1.0

    # Sample chess moves at 75%
    if "move_piece" in name:
        return 0.75

    # Sample UI operations at 50%
    if op.startswith("ui."):
        return 0.50

    # Sample other operations at 25%
    return 0.25
