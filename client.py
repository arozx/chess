import asyncio
import pickle
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from PyQt5.QtWidgets import QApplication
from online.networked_chess_board import NetworkedChessBoard
from online.network_gui import NetworkedChessBoardUI
import websockets


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
            print(f"WebSocket connection closed: {e}")
        except Exception as e:
            print(f"WebSocket error: {e}")

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
            print(f"Error handling data: {e}")

    def teardown(self):
        self.websocket_thread.stop()
        self.chess_board_ui.close()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    if len(sys.argv) != 2:
        # use production socket
        websocket_url = (
            "wss://green-pebble-140fdd8d9d1a4cc6881c9d6d7a14f0e4.azurewebsites.net/ws"
        )

    else:
        websocket_url = sys.argv[1]

    client = ChessClient(websocket_url)
    sys.exit(app.exec_())
