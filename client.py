import asyncio
import pickle
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from PyQt5.QtWidgets import QApplication
from online.networked_chess_board import NetworkedChessBoard
from online.network_gui import NetworkedChessBoardUI
import websockets
import sys
import json
import requests
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class WebSocketThread(QThread):
    data_received = pyqtSignal(bytes)

    def __init__(self, websocket_url: str):
        super().__init__()
        self.websocket_url = websocket_url
        self.websocket = None
        self.running = True

    async def connect_and_receive(self):
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                self.websocket = websocket
                while self.running:
                    data = await websocket.recv()
                    self.data_received.emit(data)
        except websockets.exceptions.ConnectionClosed as e:
            logging.error(f"WebSocket connection closed: {e}")
        except Exception as e:
            logging.error(f"WebSocket error: {e}")

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.connect_and_receive())

    def stop(self):
        self.running = False
        if self.websocket:
            asyncio.run_coroutine_threadsafe(
                self.websocket.close(), asyncio.get_event_loop()
            )
        self.quit()


class ChessClient(QObject):
    def __init__(self, websocket_url: str):
        super().__init__()
        self.chess_board = NetworkedChessBoard(is_server=False)
        self.chess_board_ui = NetworkedChessBoardUI()
        self.websocket_thread = WebSocketThread(websocket_url)

        # Connect the WebSocket thread signal to a handler
        self.websocket_thread.data_received.connect(self.handle_data)

        # Start the WebSocket thread
        self.websocket_thread.start()

        # Show the UI
        self.chess_board_ui.show()

    def handle_data(self, data: bytes):
        try:
            move = pickle.loads(data)
            self.chess_board.move_piece(*move)
            self.chess_board_ui.update_ui()
        except Exception as e:
            logging.error(f"Error handling data: {e}")

    def teardown(self):
        self.websocket_thread.stop()
        self.chess_board_ui.close()

    async def send_message(self, message_type, **kwargs):
        """Send a message to the server"""
        if not self.websocket_thread.websocket:
            logger.error("Not connected to server")
            return False

        message = {"type": message_type, **kwargs}

        try:
            await self.websocket_thread.websocket.send(json.dumps(message))
            logger.debug(f"Sent message: {message}")
            return True
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False

    async def receive_message(self):
        """Receive a message from the server"""
        if not self.websocket_thread.websocket:
            logger.error("Not connected to server")
            return None

        try:
            message = await self.websocket_thread.websocket.recv()
            return json.loads(message)
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            return None

    async def send_move(self, from_pos, to_pos):
        """Send a move to the server"""
        return await self.send_message("move", move={"from": from_pos, "to": to_pos})

    def check_server_health(self):
        """Check if the server is healthy"""
        try:
            response = requests.get(f"{self.websocket_thread.websocket_url}/health")
            if response.status_code == 200:
                logger.info(f"Server is healthy: {response.json()}")
                return True
            else:
                logger.error(f"Server returned status code {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            logger.error(
                f"Could not connect to server at {self.websocket_thread.websocket_url}"
            )
            return False


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    if len(sys.argv) != 2:
        # use production socket
        websocket_url = "wss://https://appori2n7.azurewebsites.net/ws"

    else:
        websocket_url = sys.argv[1]

    # websocket_url = "ws://localhost:8000/ws"

    client = ChessClient(websocket_url)
    sys.exit(app.exec_())
