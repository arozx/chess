import pytest
from fastapi.testclient import TestClient
from main import app
import uuid
from fastapi.websockets import WebSocketDisconnect
import asyncio

client = TestClient(app)


@pytest.fixture
def websocket_client():
    client_id = str(uuid.uuid4())
    with client.websocket_connect(f"/ws/{client_id}") as websocket:
        yield websocket


def test_websocket_connection():
    client_id = str(uuid.uuid4())
    with client.websocket_connect(f"/ws/{client_id}") as websocket:
        data = {"type": "test", "message": "Hello"}
        websocket.send_json(data)

        # Receive response without timeout parameter
        response = websocket.receive_json()
        assert response["type"] == "test_response"
        assert response["message"] == "Test received"


def test_websocket_disconnect():
    client_id = str(uuid.uuid4())
    with client.websocket_connect(f"/ws/{client_id}") as websocket:
        websocket.close()
        # Test passes if no exception is raised
