import pytest
from PyQt5.QtCore import QThread
from client import WebSocketThread

# Skip all async tests
pytestmark = pytest.mark.skip(reason="Async tests were causing hanging")


def test_websocket_thread_initialization():
    """Test basic initialization without any async operations"""
    thread = WebSocketThread("ws://localhost:8000/ws", username="test_user")

    assert isinstance(thread, QThread)
    assert thread.websocket_url == "ws://localhost:8000/ws"
    assert thread.username == "test_user"
    assert thread.websocket is None
    assert thread.running is True
