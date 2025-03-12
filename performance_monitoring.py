import time
import functools
from contextlib import contextmanager
import sentry_sdk
from typing import Optional, Any, Callable


def track_performance(
    op: str = "function",
    name: Optional[str] = None,
    tags: Optional[dict] = None,
    data: Optional[dict] = None,
) -> Callable:
    """
    Decorator to track function performance in Sentry.

    Args:
        op: Operation type (e.g., 'db', 'http', 'chess_move')
        name: Custom name for the transaction
        tags: Additional tags for the transaction
        data: Additional data to attach to the transaction
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            transaction_name = name or f"{func.__module__}.{func.__name__}"

            # Start a new transaction
            with sentry_sdk.start_transaction(
                op=op,
                name=transaction_name,
            ) as transaction:
                # Add any custom tags
                if tags:
                    for key, value in tags.items():
                        transaction.set_tag(key, value)

                # Add any custom data
                if data:
                    transaction.set_data("extra_data", data)

                start_time = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    transaction.set_status("ok")
                    return result
                except Exception as e:
                    transaction.set_status("internal_error")
                    transaction.set_data("error", str(e))
                    raise
                finally:
                    end_time = time.perf_counter()
                    duration = end_time - start_time
                    transaction.set_data("duration_seconds", duration)

        return wrapper

    return decorator


@contextmanager
def measure_operation(
    op_name: str,
    op_type: str = "operation",
    tags: Optional[dict] = None,
    data: Optional[dict] = None,
):
    """
    Context manager to measure operation performance.

    Usage:
        with measure_operation("process_move", "chess_operation", tags={"player": "white"}):
            # code to measure
    """
    with sentry_sdk.start_transaction(
        op=op_type,
        name=op_name,
    ) as transaction:
        if tags:
            for key, value in tags.items():
                transaction.set_tag(key, value)

        if data:
            transaction.set_data("extra_data", data)

        start_time = time.perf_counter()
        try:
            yield transaction
            transaction.set_status("ok")
        except Exception as e:
            transaction.set_status("internal_error")
            transaction.set_data("error", str(e))
            raise
        finally:
            end_time = time.perf_counter()
            duration = end_time - start_time
            transaction.set_data("duration_seconds", duration)


def track_slow_operations(threshold_seconds: float = 1.0) -> Callable:
    """
    Decorator to track slow operations in Sentry.
    Only creates a transaction if the operation takes longer than the threshold.

    Args:
        threshold_seconds: Time threshold in seconds
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.perf_counter() - start_time
                if duration >= threshold_seconds:
                    with sentry_sdk.start_transaction(
                        op="slow_operation",
                        name=f"{func.__module__}.{func.__name__}",
                    ) as transaction:
                        transaction.set_data("duration_seconds", duration)
                        transaction.set_tag("threshold_seconds", threshold_seconds)

        return wrapper

    return decorator
