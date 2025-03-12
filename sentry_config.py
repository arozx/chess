import os
import sentry_sdk
from dotenv import load_dotenv


def init_sentry():
    """Initialize Sentry SDK with configuration."""
    load_dotenv()

    # Get Sentry DSN from environment variable
    sentry_dsn = os.getenv("SENTRY_DSN")

    if not sentry_dsn:
        print(
            "Warning: SENTRY_DSN not found in environment variables. Sentry will not be initialized."
        )
        return

    sentry_sdk.init(
        dsn=sentry_dsn,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=1.0,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        profiles_sample_rate=1.0,
        # Enable performance monitoring
        enable_tracing=True,
        # Environment name
        environment=os.getenv("ENVIRONMENT", "development"),
        # Add your chess game version
        release="chess-game@1.0.0",
    )
