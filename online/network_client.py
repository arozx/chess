import asyncio
import pickle
import sys
import threading
import websockets

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal

from online.networked_chess_board import NetworkedChessBoard
from online.network_gui import NetworkedChessBoardUI


class ChessClient(QObject):
    data_received = pyqtSignal(object)

    def __init__(self, host="localhost", port=5556):
        super().__init__()
        self.uri = f"ws://{host}:{port}"
        self.chess_board = NetworkedChessBoard(is_server=False)
        self.chess_board_ui = NetworkedChessBoardUI()
        self.websocket = None

        self.data_received.connect(self.handle_data)
        threading.Thread(target=self.start_client()).start()

    def start_client(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.connect_to_server())

    async def connect_to_server(self):
        async with websockets.connect(self.uri) as websocket:
            self.websocket = websocket
            self.chess_board_ui.show()
            await self.receive_data()

    async def receive_data(self):
        while True:
            try:
                data = await self.websocket.recv()
                move = pickle.loads(data)
                self.data_received.emit(move)
            except Exception as e:
                print(f"Error: {e}")
                break

    def handle_data(self, move):
        self.chess_board.move_piece(*move)
        self.chess_board_ui.update_ui()

    def teardown(self):
        if self.websocket:
            asyncio.run(self.websocket.close())
        self.chess_board_ui.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    client = ChessClient()
    sys.exit(app.exec_())
