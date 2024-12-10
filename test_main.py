import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@pytest.fixture
def websocket_client():
    with client.websocket_connect("/ws") as websocket:
        yield websocket


def test_websocket_connection(websocket_client):
    assert websocket_client


def test_websocket_disconnect():
    with client.websocket_connect("/ws") as websocket:
        websocket.close()
