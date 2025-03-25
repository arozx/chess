import pickle
from logging import getLogger
from PyQt5.QtWidgets import (
    QLabel,
    QPushButton,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from gui import ChessBoardUI
from online.networked_chess_board import NetworkedChessBoard

logger = getLogger(__name__)

# Try to import sentry_sdk, but don't fail if it's not available
try:
    import sentry_sdk

    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    logger.warning("Sentry SDK not available. Error tracking will be disabled.")


class ChessPiece(QLabel):
    def __init__(self, parent=None, piece=None):
        super().__init__(parent)
        self.setFixedSize(60, 60)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: transparent; margin: 0; padding: 0;")
        if piece:
            pixmap = QPixmap(
                f"media/{piece.colour}/{piece.__class__.__name__.upper()[0:1]}{piece.__class__.__name__.lower()[1::]}.svg"
            )
            scaled_pixmap = pixmap.scaled(
                55, 55, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.setPixmap(scaled_pixmap)


class NetworkedChessBoardUI(ChessBoardUI):
    def __init__(self):
        super().__init__()
        self.chess_board = NetworkedChessBoard(is_server=False)
        self.status_label = QLabel("White to move")
        self.status_label.setStyleSheet(
            "color: white; font-size: 14px; margin-bottom: 15px;"
        )
        self.status_label.setAlignment(Qt.AlignCenter)
        self.move_count_label = QLabel("Move: 0")
        self.move_count_label.setStyleSheet("font-size: 12px; color: #9e9e9e;")
        self.export_button = QPushButton("Export Game")
        self.export_button.setStyleSheet(
            """
            QPushButton {
                background-color: rgb(51, 51, 51);
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                color: white;
            }
            QPushButton:hover {
                background-color: rgb(60, 60, 60);
            }
        """
        )
        self.move_history_label = QLabel("Move History")
        self.move_history_label.setStyleSheet(
            "font-size: 12px; color: #9e9e9e; margin-top: 15px;"
        )
        self.move_history = [QLabel("") for _ in range(10)]
        for label in self.move_history:
            label.setStyleSheet("font-size: 11px; color: white; margin: 2px 0;")
            label.setAlignment(Qt.AlignLeft)
        self.current_white_move = None
        self.selected_piece = None
        self.selected_pos = None
        self.init_main_ui()

    def init_main_ui(self):
        try:
            if SENTRY_AVAILABLE:
                with sentry_sdk.start_span(
                    op="gui.init_main", description="Initialize main UI"
                ):
                    self._init_main_ui_impl()
            else:
                self._init_main_ui_impl()
        except Exception as e:
            logger.error(f"Error initializing main UI: {e}")
            if SENTRY_AVAILABLE:
                sentry_sdk.capture_exception(e)
            raise

    def _init_main_ui_impl(self):
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        self.setStyleSheet("background-color: rgb(44, 44, 44);")
        main_layout = QHBoxLayout(self.main_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        left_panel = QVBoxLayout()
        left_panel.setSpacing(0)
        left_panel.addWidget(self.status_label)
        self.theme = self.parse_ini("theme.ini")
        light_squares = self.theme["light_squares"]["colour"]
        dark_squares = self.theme["dark_squares"]["colour"]
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(0)
        self.grid_layout.setHorizontalSpacing(0)
        self.grid_layout.setVerticalSpacing(0)
        self.init_chessboard(light_squares, dark_squares)
        left_panel.addLayout(self.grid_layout)
        right_panel = QVBoxLayout()
        right_panel.setSpacing(5)
        right_panel.setContentsMargins(10, 0, 0, 0)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(10)
        info_layout.addWidget(self.move_count_label)
        info_layout.addWidget(self.export_button)
        right_panel.addLayout(info_layout)
        history_container = QVBoxLayout()
        history_container.setSpacing(5)
        history_container.addWidget(self.move_history_label)
        for label in self.move_history:
            label.setStyleSheet(
                """
                font-family: 'Courier New', monospace;
                font-size: 12px;
                color: white;
                margin: 3px 0;
                padding: 2px 5px;
                background-color: rgb(51, 51, 51);
                border-radius: 2px;
            """
            )
            label.setMinimumWidth(250)
            history_container.addWidget(label)
        right_panel.addLayout(history_container)
        right_panel.addStretch()
        main_layout.addLayout(left_panel, stretch=4)
        main_layout.addLayout(right_panel, stretch=1)
        self.setFixedSize(800, 650)
        self.setWindowTitle("Chess")
        self.setStyleSheet("background-color: rgb(44, 44, 44);")
        self.show()

    def handle_click(self, row, col):
        try:
            widget = self.grid_layout.itemAtPosition(row, col).widget()
            if widget.layout() and widget.layout().count() > 0:
                piece = self.chess_board.board[row][col]
                if piece:
                    if self.selected_piece:
                        if piece.colour != self.selected_piece.colour:
                            self.try_move(row, col)
                        else:
                            self.selected_piece = piece
                            self.selected_pos = (row, col)
                    else:
                        self.selected_piece = piece
                        self.selected_pos = (row, col)
            else:
                if self.selected_piece:
                    self.try_move(row, col)
        except Exception as e:
            logger.error(f"Error handling click: {e}")

    def try_move(self, target_row, target_col):
        if not self.selected_piece or not self.selected_pos:
            return
        source_row, source_col = self.selected_pos
        moving_piece = self.selected_piece
        if self.chess_board.move_piece(source_row, source_col, target_row, target_col):
            # If successful, send the move to the server via the client
            if hasattr(self, "client"):
                self.client.send_move(
                    {"row": source_row, "col": source_col},
                    {"row": target_row, "col": target_col},
                )
            self.update_ui()
            self.selected_piece = None
            self.selected_pos = None
            self.status_label.setText(
                f"{self.chess_board.player_turn.capitalize()} to move"
            )
            self.move_count_label.setText(f"Move: {self.chess_board.move_count}")
            move_notation = f"{moving_piece.__class__.__name__[0]} {chr(97 + source_col)}{source_row + 1}-{chr(97 + target_col)}{target_row + 1}"
            move_number = (self.chess_board.move_count + 1) // 2
            if moving_piece.colour == "white":
                for i in range(len(self.move_history) - 1, 0, -1):
                    current_text = self.move_history[i - 1].text()
                    if current_text:
                        self.move_history[i].setText(current_text)
                self.current_white_move = f"{move_number}. {move_notation}"
                self.move_history[0].setText(self.current_white_move)
            else:
                if self.current_white_move:
                    full_move = f"{self.current_white_move:<30}{move_notation}"
                    self.move_history[0].setText(full_move)
                    self.current_white_move = None
            for label in self.move_history:
                label.setStyleSheet(
                    """
                    font-family: 'Courier New', monospace;
                    font-size: 12px;
                    color: white;
                    margin: 3px 0;
                    padding: 2px 5px;
                    background-color: rgb(51, 51, 51);
                    border-radius: 2px;
                """
                )
                label.setMinimumWidth(250)
                label.setAlignment(Qt.AlignLeft)
            logger.debug("Current move history:")
            for i, label in enumerate(self.move_history):
                logger.debug(f"Move {i}: {label.text()}")

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
                logger.error(f"Error: {e}")
                break

    def update_ui(self):
        for row in range(8):
            for col in range(8):
                button = self.grid_layout.itemAtPosition(row, col).widget()
                while button.layout().count():
                    child = button.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                piece = self.chess_board.board[row][col]
                if piece:
                    piece_label = ChessPiece(piece=piece)
                    button.layout().addWidget(piece_label)

    def set_client(self, client):
        self.client = client
