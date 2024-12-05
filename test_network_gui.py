import pytest
from PyQt5.QtWidgets import QApplication, QGridLayout
from online.network_gui import NetworkedChessBoardUI
from online.networked_chess_board import NetworkedChessBoard
import threading
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from online.network_gui import ChessPiece
import pickle


@pytest.fixture(scope="module")
def app():
    return QApplication([])

@pytest.fixture
def chess_board():
    return NetworkedChessBoard(host="localhost", port=5556, is_server=False)

@pytest.fixture
def networked_chess_board_ui(chess_board):
    ui = NetworkedChessBoardUI()
    ui.chess_board = chess_board
    ui.grid_layout = QGridLayout()
    for row in range(8):
        for col in range(8):
            button = QWidget()
            button.setLayout(QVBoxLayout())
            ui.grid_layout.addWidget(button, row, col)
    return ui

def test_update_ui(networked_chess_board_ui):
    # Mock some pieces on the board
    networked_chess_board_ui.chess_board.board[0][0] = ChessPiece(piece="rook")
    networked_chess_board_ui.chess_board.board[1][1] = ChessPiece(piece="knight")
    networked_chess_board_ui.update_ui()

    # Check if the pieces are added to the UI
    assert (
        networked_chess_board_ui.grid_layout.itemAtPosition(0, 0)
        .widget()
        .layout()
        .count()
        == 1
    )
    assert (
        networked_chess_board_ui.grid_layout.itemAtPosition(1, 1)
        .widget()
        .layout()
        .count()
        == 1
    )

def test_receive_data(networked_chess_board_ui, monkeypatch):
    # Mock socket to simulate receiving data
    class MockSocket:
        def __init__(self):
            self.data = pickle.dumps(((0, 0), (1, 1)))

        def recv(self):
            return self.data

    monkeypatch.setattr(networked_chess_board_ui.chess_board, "socket", MockSocket())

    def run_receive_data():
        networked_chess_board_ui.receive_data()

    thread = threading.Thread(target=run_receive_data)
    thread.start()
    thread.join(timeout=1)

    # Check if the move was made
    assert networked_chess_board_ui.chess_board.board[1][1] is not None
    assert networked_chess_board_ui.chess_board.board[0][0] is None
