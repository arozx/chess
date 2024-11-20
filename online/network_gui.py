import pickle
import sys

from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

from online.networked_chess_board import NetworkedChessBoard
from gui import ChessBoardUI


class ChessPiece(QLabel):
    def __init__(self, parent=None, piece=None):
        super().__init__(parent)
        self.setFixedSize(60, 60)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: transparent;")
        if piece:
            pixmap = QPixmap(
                f"media/{piece.colour}/{piece.__class__.__name__.upper()[0:1]}{piece.__class__.__name__.lower()[1::]}.svg"
            )
            scaled_pixmap = pixmap.scaled(
                60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.setPixmap(scaled_pixmap)


class NetworkedChessBoardUI(ChessBoardUI):
    def __init__(self, chess_board, host="localhost", port=5556, is_server=False):
        super().__init__()

    def receive_data(self):
        while True:
            try:
                data = self.chess_board.socket.recv(4096)
                if not data:
                    break
                move = pickle.loads(data)
                self.chess_board.move_piece(*move)
                self.update_ui()
            except Exception as e:
                print(f"Error: {e}")
                break

    def update_ui(self):
        for row in range(8):
            for col in range(8):
                button = self.grid_layout.itemAtPosition(row, col).widget()
                # Clear the button layout
                while button.layout().count():
                    child = button.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                # Add the piece to the button if it exists
                piece = self.chess_board.board[row][col]
                if piece:
                    piece_label = ChessPiece(piece=piece)
                    button.layout().addWidget(piece_label)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    chess_board = NetworkedChessBoard(host="localhost", port=5555, is_server=False)
    window = NetworkedChessBoardUI()
    window.show()
    sys.exit(app.exec_())
