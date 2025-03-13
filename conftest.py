import pytest


# Configure pytest-asyncio to use function scope for event loops
@pytest.fixture(scope="function")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    import asyncio

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
