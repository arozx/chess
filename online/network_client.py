import threading
import pickle
import socket
import sys

from online.networked_chess_board import NetworkedChessBoard
from online.network_gui import NetworkedChessBoardUI

from PyQt5.QtWidgets import QApplication


class ChessClient:
    def __init__(self, host="localhost", port=5556):
        self.chess_board = NetworkedChessBoard(host=host, port=port, is_server=False)
        self.chess_board.socket.settimeout(5)  # Set a timeout for the client socket
        self.chess_board_ui = NetworkedChessBoardUI(self.chess_board)
        threading.Thread(target=self.receive_data).start()

    def receive_data(self):
        while True:
            try:
                data = self.chess_board.socket.recv(4096)
                if not data:
                    break
                move = pickle.loads(data)
                self.chess_board.move_piece(*move)
                self.chess_board_ui.update_ui()
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Error: {e}")
                break

    def teardown(self):
        # delete connection and cleanup
        self.chess_board.socket.close()
        if hasattr(self.chess_board, "receive_thread"):
            self.chess_board.receive_thread.join()

        self.chess_board_ui.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    client = ChessClient()
    client.chess_board_ui.show()
    sys.exit(app.exec_())
