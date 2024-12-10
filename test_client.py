import pytest
from PyQt5.QtCore import QThread
from client import WebSocketThread
import asyncio
from unittest.mock import patch, AsyncMock


@pytest.fixture
def websocket_thread():
    return WebSocketThread("ws://localhost:8000/ws")


def test_websocket_thread_initialization(websocket_thread):
    assert isinstance(websocket_thread, QThread)
    assert websocket_thread.websocket_url == "ws://localhost:8000/ws"
    assert websocket_thread.websocket is None
    assert websocket_thread.running is True


def test_websocket_thread_run(websocket_thread):
    with patch.object(asyncio, "new_event_loop", return_value=asyncio.get_event_loop()):
        with patch.object(asyncio.get_event_loop(), "run_until_complete") as mock_run:
            websocket_thread.run()
            mock_run.assert_called_once()


def test_websocket_thread_stop(websocket_thread):
    websocket_thread.running = True
    websocket_thread.websocket = AsyncMock()
    websocket_thread.websocket.close = AsyncMock()

    with patch("asyncio.run_coroutine_threadsafe") as mock_run_coroutine:
        websocket_thread.stop()
        assert websocket_thread.running is False
        mock_run_coroutine.assert_called_once()
        websocket_thread.websocket.close.assert_called_once()
