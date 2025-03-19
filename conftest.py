import pytest
import asyncio


def pytest_configure(config):
    """Configure pytest options."""
    config.option.asyncio_mode = "strict"
    config.option.asyncio_default_fixture_loop_scope = "function"


@pytest.fixture(scope="function")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
