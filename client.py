import asyncio
import pickle
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from PyQt5.QtWidgets import QApplication
from online.networked_chess_board import NetworkedChessBoard
from online.network_gui import NetworkedChessBoardUI
from login_window import LoginWindow
import websockets
import sys
import json
import logging
import uuid

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class WebSocketThread(QThread):
    data_received = pyqtSignal(bytes)
    move_to_send = None

    def __init__(self, websocket_url: str, username: str):
        super().__init__()
        self.websocket_url = websocket_url
        self.username = username
        self.websocket = None
        self.running = True

    async def connect_and_receive(self):
        """Main async method for websocket operations"""
        async with websockets.connect(self.websocket_url) as websocket:
            self.websocket = websocket
            while self.running:
                try:
                    # Use _ for unused variable
                    _ = await websocket.receive()
                    # Handle message...
                except Exception:
                    self.running = False
                    break

    async def stop(self):
        """Async method to stop the websocket connection"""
        self.running = False
        if self.websocket:
            await self.websocket.close()

    def run(self):
        """Run in thread context"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.connect_and_receive())

    def queue_move(self, move_data):
        """Queue a move to be sent in the websocket thread"""
        self.move_to_send = move_data


class ChessClient(QObject):
    def __init__(self, websocket_url: str, username: str):
        super().__init__()
        self.username = username
        self.chess_board = NetworkedChessBoard(is_server=False)
        self.chess_board_ui = NetworkedChessBoardUI()
        self.websocket_thread = WebSocketThread(websocket_url, username)

        # Connect the WebSocket thread signal to a handler
        self.websocket_thread.data_received.connect(self.handle_data)

        # Set the client reference in the UI
        self.chess_board_ui.set_client(self)

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

        message = {"type": message_type, "username": self.username, **kwargs}

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

    def send_move(self, from_pos, to_pos):
        """Send a move to the server synchronously"""
        message = {
            "type": "move",
            "username": self.username,
            "move": {"from": from_pos, "to": to_pos},
        }
        self.websocket_thread.queue_move(message)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Create and show login window
    login_window = LoginWindow()

    def start_chess_client(username):
        # Get the websocket URL
        if len(sys.argv) != 2:
            # use production socket
            server_url = "wss://appori2n7.azurewebsites.net/ws"
        else:
            server_url = sys.argv[1]

        # server_url = "ws://localhost:8000/ws"

        # Add client ID to the WebSocket URL
        client_id = str(uuid.uuid4())
        if not server_url.endswith("/"):
            server_url += "/"
        full_url = server_url + client_id

        # Create chess client with authenticated username
        global client
        client = ChessClient(full_url, username)

    # Connect login success signal to start_chess_client
    login_window.login_successful.connect(start_chess_client)
    login_window.show()

    sys.exit(app.exec_())
