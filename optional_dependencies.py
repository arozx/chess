import logging

logger = logging.getLogger(__name__)


class OptionalDependencyWarning:
    def __init__(self, dependency_name):
        self.dependency_name = dependency_name
        self.warning_message = (
            f"{dependency_name} is not installed. Some features will be disabled."
        )
        logger.warning(self.warning_message)


# Sentry SDK
try:
    import sentry_sdk
    from sentry_sdk import get_current_scope

    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    sentry_sdk = OptionalDependencyWarning("sentry-sdk")

    # Replace lambda with proper function definition
    def get_current_scope():
        return None


# PostgreSQL
try:
    import psycopg2
    import psycopg2.pool

    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    psycopg2 = OptionalDependencyWarning("psycopg2")
