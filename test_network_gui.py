import pytest
from PyQt5.QtWidgets import QApplication, QGridLayout
from online.network_gui import NetworkedChessBoardUI
from online.networked_chess_board import NetworkedChessBoard
import threading


@pytest.fixture(scope="module")
def app():
    app = QApplication([])
    yield app
    app.quit()


@pytest.fixture(scope="module")
def server():
    server_board = NetworkedChessBoard(host="localhost", port=5555, is_server=True)
    server_thread = threading.Thread(target=server_board.receive_data)
    server_thread.start()
    yield server_board
    server_board.socket.close()
    server_thread.join()


@pytest.fixture
def chess_board():
    return NetworkedChessBoard(host="localhost", port=5555, is_server=False)


@pytest.fixture
def ui(chess_board):
    return NetworkedChessBoardUI(chess_board)


def test_ui_initialization(ui):
    assert ui.move_count_label.text() == "Move count: 0"
    assert ui.clock_label.text() == "Elapsed time: 0.00 seconds"
    assert ui.material_count_label.text() == "Material count: 0"
    assert ui.player_to_move_label.text() == "White to move"
    assert isinstance(ui.grid_layout, QGridLayout)


def test_login_ui_initialization(ui):
    assert ui.username_label.text() == "Username:"
    assert ui.password_label.text() == "Password:"
    assert ui.login_button.text() == "Login"


def test_handle_login_success(ui, mocker):
    mocker.patch.object(ui.db_connector, "verify_user", return_value=True)
    mocker.patch.object(ui.db_connector, "insert_login_attempt")
    mocker.patch.object(ui, "show_main_ui")

    ui.username_input.setText("test_user")
    ui.password_input.setText("test_password")
    ui.handle_login()

    ui.db_connector.verify_user.assert_called_once_with("test_user", "test_password")
    ui.db_connector.insert_login_attempt.assert_called_once()
    ui.show_main_ui.assert_called_once()


def test_handle_login_failure(ui, mocker):
    mocker.patch.object(ui.db_connector, "verify_user", return_value=False)
    mocker.patch("builtins.print")

    ui.username_input.setText("test_user")
    ui.password_input.setText("test_password")
    ui.handle_login()

    ui.db_connector.verify_user.assert_called_once_with("test_user", "test_password")
    print.assert_called_once_with("Invalid username or password")


def test_update_clock(ui, mocker):
    mocker.patch("time.time", return_value=1000)
    ui.chess_board.start_time = 900
    ui.update_clock()
    assert ui.clock_label.text() == "Elapsed time: 100.00 seconds"


def test_handle_click(ui, mocker):
    mocker.patch.object(ui.chess_board, "move_piece", return_value=True)
    mocker.patch.object(ui, "move_piece")
    ui.selected_piece = None
    ui.handle_click(0, 0)
    assert ui.selected_piece is not None

    ui.selected_piece = mocker.Mock()
    ui.handle_click(0, 1)
    ui.move_piece.assert_called_once_with(target_row=0, target_col=1)
