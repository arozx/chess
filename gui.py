import configparser
import time
import sys
from logging_config import configure_logging, get_logger
from sentry_config import init_sentry
import sentry_sdk
from sentry_sdk import get_current_scope
from performance_monitoring import (
    track_performance,
    measure_operation,
    track_slow_operations,
)

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QGridLayout,
    QWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap

# From the application
from chess_board_1 import ChessBoard
from postgres_auth import DBConnector

# Initialize Sentry first
init_sentry()

# Configure logging
logger = get_logger(__name__)


class ChessPiece(QLabel):
    """
    Creates a QLabel widget to display a chess piece
    """

    def __init__(self, parent=None, piece=None):
        try:
            with sentry_sdk.start_span(
                op="ui.create_piece", description="Create chess piece widget"
            ) as _:
                super().__init__(parent)
                self.setFixedSize(60, 60)
                self.setAlignment(Qt.AlignCenter)
                self.setStyleSheet("background-color: transparent;")
                if piece:
                    _.set_tag("piece_type", piece.__class__.__name__)
                    _.set_tag("piece_color", piece.colour)
                    pixmap = QPixmap(
                        f"media/{piece.colour}/{piece.__class__.__name__.upper()[0:1]}{piece.__class__.__name__.lower()[1::]}.svg"
                    )
                    scaled_pixmap = pixmap.scaled(
                        60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                    self.setPixmap(scaled_pixmap)
        except Exception as e:
            logger.error(f"Error creating chess piece widget: {e}")
            sentry_sdk.capture_exception(e)
            raise


class ChessBoardUI(QMainWindow):
    """
    Main window for the chess game
    """

    def __init__(self):
        with measure_operation("init_ui", "ui_initialization"):
            super().__init__()
            logger.info("Initializing Chess Game UI")

            # Set UI context for Sentry
            scope = get_current_scope()
            scope.set_tag("component", "frontend")
            scope.set_tag("ui_state", "initializing")

            self.setWindowTitle("Chess Game")
            self.setGeometry(100, 100, 900, 600)

            # Database setup
            self.db_connector = DBConnector()
            self.db_connector.create_users_table()
            self.db_connector.create_logins_table()
            self.db_connector.create_games_table()  # Create games table
            self.current_game_id = None
            self.player1 = "White"
            self.player2 = "Black"

            # Initialize variables
            self.init_game_state()

            # Set UI ready state
            scope.set_tag("ui_state", "ready")

    def init_game_state(self):
        """Initialize game state with Sentry monitoring"""
        try:
            with sentry_sdk.start_span(
                op="ui.init_game", description="Initialize game state"
            ):
                self.chess_board = ChessBoard()
                self.selected_piece = None
                self.selected_pos = None
                self.move_history = []

                # Initialize game in database
                self.current_game_id = self.start_new_game()

                # Track game state in Sentry
                scope = get_current_scope()
                scope.set_tag("game_state", "new_game")
                scope.set_context(
                    "game_info",
                    {
                        "move_count": 0,
                        "player_turn": "white",
                        "selected_piece": None,
                    },
                )
        except Exception as e:
            logger.error(f"Error initializing game state: {e}")
            sentry_sdk.capture_exception(e)
            raise

    def start_new_game(self):
        """
        Initialize a new game in the database
        """
        try:
            with sentry_sdk.start_span(
                op="db.start_game", description="Start new game"
            ) as _:
                # Save initial board state
                self.db_connector.insert_game(
                    self.player1,
                    self.player2,
                    self.chess_board.board_array_to_fen(),
                )
        except Exception as e:
            logger.error(f"Error starting new game: {e}")
            sentry_sdk.capture_exception(e)
            raise

    def end_game(self):
        """
        Save the final game state to the database
        """
        try:
            with sentry_sdk.start_span(op="db.end_game", description="End game") as _:
                # Save final board state
                self.db_connector.insert_game(
                    self.player1,
                    self.player2,
                    self.chess_board.board_array_to_fen(),
                )
        except Exception as e:
            logger.error(f"Error ending game: {e}")
            sentry_sdk.capture_exception(e)
            raise

    def init_login_ui(self):
        try:
            with sentry_sdk.start_span(
                op="gui.init_login", description="Initialize login UI"
            ):
                self.login_widget = QWidget(self)
                login_layout = QVBoxLayout(self.login_widget)

                self.setStyleSheet("background-color: rgb(44, 44, 44);")

                # Login fields
                self.username_label = QLabel("Username:")
                self.username_label.setStyleSheet("color: white; font-weight: bold;")
                self.username_input = QLineEdit()
                self.username_input.setStyleSheet(
                    "background-color: white; color: black; padding: 5px; border-radius: 4px;"
                )

                self.password_label = QLabel("Password:")
                self.password_label.setStyleSheet("color: white; font-weight: bold;")
                self.password_input = QLineEdit()
                self.password_input.setStyleSheet(
                    "background-color: white; color: black; padding: 5px; border-radius: 4px;"
                )
                self.password_input.setEchoMode(QLineEdit.Password)

                self.login_button = QPushButton("Login")
                self.login_button.setStyleSheet(
                    """
                    QPushButton {
                        background-color: rgb(51, 51, 51);
                        color: white;
                        padding: 8px 16px;
                        border: none;
                        border-radius: 4px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: rgb(60, 60, 60);
                    }
                    QPushButton:pressed {
                        background-color: rgb(40, 40, 40);
                    }
                """
                )
                self.login_button.clicked.connect(self.handle_login)

                # Add widgets to layout
                login_layout.addWidget(self.username_label)
                login_layout.addWidget(self.username_input)
                login_layout.addWidget(self.password_label)
                login_layout.addWidget(self.password_input)
                login_layout.addWidget(self.login_button)

                # Center the login form
                login_layout.setAlignment(Qt.AlignCenter)
                login_layout.setContentsMargins(50, 50, 50, 50)
                login_layout.setSpacing(10)

                # Set the login widget as central
                self.setCentralWidget(self.login_widget)
        except Exception as e:
            logger.error(f"Error initializing login UI: {e}")
            sentry_sdk.capture_exception(e)
            raise

    def export(self):
        try:
            with sentry_sdk.start_span(op="gui.export", description="Export game"):
                self.chess_board.board_array_to_pgn()
        except Exception as e:
            logger.error(f"Error exporting game: {e}")
            sentry_sdk.capture_exception(e)
            QMessageBox.warning(self, "Export Failed", "Failed to export the game")

    def handle_login(self):
        try:
            with sentry_sdk.start_span(
                op="gui.handle_login", description="Handle user login"
            ) as _:
                username = self.username_input.text()
                _.set_tag("username", username)
                logger.info(f"Login attempt: {username}")

                if self.db_connector.verify_user(username, self.password_input.text()):
                    logger.info(f"User {username} logged in successfully")
                    self.db_connector.insert_login_attempt(username, time.time())
                    self.init_main_ui()  # Switch to the main UI
                else:
                    logger.warning(f"Invalid login attempt for user {username}")
                    QMessageBox.warning(
                        self, "Login Failed", "Invalid username or password"
                    )
        except Exception as e:
            logger.error(f"Error during login: {e}")
            sentry_sdk.capture_exception(e)
            QMessageBox.critical(self, "Error", "An error occurred during login")

    def init_main_ui(self):
        try:
            with sentry_sdk.start_span(
                op="gui.init_main", description="Initialize main UI"
            ):
                self.main_widget = QWidget(self)
                self.setCentralWidget(self.main_widget)

                # Main layout
                main_layout = QHBoxLayout(self.main_widget)

                # Left panel (Chessboard + labels)
                left_panel = QVBoxLayout()
                left_panel.addWidget(self.move_count_label)
                left_panel.addWidget(self.clock_label)
                left_panel.addWidget(self.material_count_label)
                left_panel.addWidget(self.player_to_move_label)
                left_panel.addWidget(self.opening_label)

                # Buttons
                left_panel.addWidget(self.export_button)

                # Load theme config from file
                self.theme = self.parse_ini("theme.ini")

                # extract light and dark squares
                light_squares = self.theme["light_squares"]["colour"]
                dark_squares = self.theme["dark_squares"]["colour"]

                # Chessboard grid
                self.grid_layout = QGridLayout()
                self.init_chessboard(light_squares, dark_squares)
                left_panel.addLayout(self.grid_layout)

                # Right panel (Move history)
                right_panel = QVBoxLayout()
                for label in self.move_history_labels:
                    right_panel.addWidget(label)

                # Combine layouts
                main_layout.addLayout(left_panel)
                main_layout.addLayout(right_panel)

                self.start_timer()
                self.show()
        except Exception as e:
            logger.error(f"Error initializing main UI: {e}")
            sentry_sdk.capture_exception(e)
            raise

    def init_chessboard(self, light_squares="#f0d9b5", dark_squares="#b58863"):
        """
        Create the chessboard grid layout
        """
        for row in range(8):
            for col in range(8):
                button = QPushButton()
                button.setFixedSize(60, 60)
                button.setStyleSheet(
                    f"background-color: {light_squares if (row + col) % 2 == 0 else dark_squares}; border: none;"
                )
                button.clicked.connect(lambda _, r=row, c=col: self.handle_click(r, c))
                button.setLayout(QVBoxLayout())
                button.layout().setAlignment(Qt.AlignCenter)
                self.grid_layout.addWidget(button, row, col)

                # Add chess pieces
                piece = self.chess_board.board[row][col]
                if piece:
                    piece_label = ChessPiece(piece=piece)
                    button.layout().addWidget(piece_label)

    def parse_ini(self, file_path):
        """
        Use configParser to parse theme.ini
        return the users theme configuration as a dict
        """

        config = configparser.ConfigParser()
        config.read(file_path)

        # Convert sections to a dictionary
        parsed_data = {section: dict(config[section]) for section in config.sections()}
        return parsed_data

    def handle_click(self, row, col):
        try:
            with sentry_sdk.start_span(
                op="ui.handle_click",
                description=f"Handle board click at ({row}, {col})",
            ) as _:
                _.set_tag("click_position", f"{row},{col}")
                _.set_tag("player_turn", self.chess_board.player_turn)

                # Start transaction for move attempt
                with sentry_sdk.start_transaction(
                    op="ui.move", name="Chess Move Attempt", sampled=True
                ) as transaction:
                    widget = self.grid_layout.itemAtPosition(row, col).widget()

                    # Track click state
                    transaction.set_tag(
                        "has_piece",
                        bool(
                            widget.layout()
                            and isinstance(
                                widget.layout().itemAt(0).widget(), ChessPiece
                            )
                        ),
                    )

                    if widget.layout() and isinstance(
                        widget.layout().itemAt(0).widget(), ChessPiece
                    ):
                        piece = widget.layout().itemAt(0).widget()
                        piece_obj = self.chess_board.board[row][col]

                        # Track piece selection
                        transaction.set_data(
                            "piece_type",
                            piece_obj.__class__.__name__ if piece_obj else None,
                        )
                        transaction.set_data(
                            "piece_color", piece_obj.colour if piece_obj else None
                        )

                        if (
                            piece_obj
                            and piece_obj.colour != self.chess_board.player_turn
                        ):
                            logger.warning(
                                f"Wrong turn: attempted {piece_obj.colour} during {self.chess_board.player_turn}'s turn"
                            )
                            sentry_sdk.capture_message(
                                "Invalid turn attempt",
                                level="warning",
                                extras={
                                    "attempted_color": piece_obj.colour,
                                    "current_turn": self.chess_board.player_turn,
                                },
                            )
                            return

                        if self.selected_piece:
                            self.move_piece(target_row=row, target_col=col)
                        else:
                            self.selected_piece = piece
                            self.selected_pos = (row, col)
                            logger.info(f"Selected piece at ({row}, {col})")
                    elif self.selected_piece:
                        self.move_piece(target_row=row, target_col=col)

        except Exception as e:
            logger.error(f"Error handling click: {e}")
            sentry_sdk.capture_exception(e)

    def move_piece(
        self, source_row=None, source_col=None, target_row=None, target_col=None
    ):
        try:
            with sentry_sdk.start_span(
                op="ui.move_piece", description="Move chess piece"
            ) as _:
                if source_row is None or source_col is None:
                    source_row, source_col = self.selected_pos

                _.set_tag("source", f"{source_row},{source_col}")
                _.set_tag("target", f"{target_row},{target_col}")
                _.set_tag("player_turn", self.chess_board.player_turn)

                # Track move attempt
                piece = self.chess_board.board[source_row][source_col]
                if piece:
                    _.set_tag("piece_type", piece.__class__.__name__)
                    _.set_tag("piece_color", piece.colour)

                move_start_time = time.time()
                move_success = self.chess_board.move_piece(
                    source_row, source_col, target_row, target_col
                )
                move_duration = time.time() - move_start_time

                # Track move performance
                _.set_data("move_duration", move_duration)
                _.set_data("move_success", move_success)

                if move_success:
                    self.update_ui_after_move(
                        source_row, source_col, target_row, target_col
                    )

                    # Track successful move
                    sentry_sdk.set_tag("last_move_success", True)
                    if move_duration > 0.5:  # Log slow moves
                        sentry_sdk.capture_message(
                            "Slow move detected",
                            level="warning",
                            extras={"move_duration": move_duration},
                        )
                else:
                    # Track failed move
                    sentry_sdk.set_tag("last_move_success", False)
                    sentry_sdk.capture_message(
                        "Invalid move attempted",
                        level="info",
                        extras={
                            "source": f"{source_row},{source_col}",
                            "target": f"{target_row},{target_col}",
                            "piece_type": piece.__class__.__name__ if piece else None,
                        },
                    )

                self.selected_piece = None
                self.selected_pos = None

        except Exception as e:
            logger.error(f"Error moving piece: {e}")
            sentry_sdk.capture_exception(e)

    @track_performance(op="ui", name="update_ui")
    def update_ui_after_move(self, source_row, source_col, target_row, target_col):
        with measure_operation("update_board_display", "ui_update"):
            # Update the board display
            self.update_board_display()

        with measure_operation("update_move_history", "ui_update"):
            # Update move history
            self.update_move_history(source_row, source_col, target_row, target_col)

        with measure_operation("update_clock", "ui_update"):
            # Update the clock
            self.update_clock()

        # Check if game has ended after the move
        if self.chess_board.is_game_over():
            self.end_game()

    @track_slow_operations(threshold_seconds=0.1)
    def update_board_display(self):
        # ... existing code ...
        pass

    @track_performance(op="ui", name="update_move_history")
    def update_move_history(self, source_row, source_col, target_row, target_col):
        """
        Update the move history on the right panel
        """

        def to_chess_notation(row, col):
            """
            Convert row and column indices to chess notation
            """
            return f"{chr(97 + col)}{row + 1}"  # 'a'-'h' for columns, 1-8 for rows

        source_notation = to_chess_notation(source_row, source_col)
        target_notation = to_chess_notation(target_row, target_col)

        current_player = "Black" if self.chess_board.player_turn == "white" else "White"

        move = f"{current_player}: {source_notation} → {target_notation}"

        # Shift previous moves down the history
        for i in range(len(self.move_history_labels) - 1, 0, -1):
            self.move_history_labels[i].setText(self.move_history_labels[i - 1].text())

        # Add the new move at the top
        self.move_history_labels[0].setText(move)

        self.save_move()

    @track_performance(op="database", name="save_move")
    def save_move(self):
        """
        Save the move history
        """
        self.db_connector.insert_game(
            self.player1, self.player2, self.move_history_labels[0].text()
        )

    def start_timer(self):
        """
        Start the timer
        """
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(10)

    def update_clock(self):
        """
        Update the clock label
        """
        elapsed_time = time.time() - self.chess_board.start_time
        self.clock_label.setText(f"Elapsed time: {elapsed_time:.2f} seconds")

    @track_performance(op="ai", name="ai_move_calculation")
    def ai_move(self):
        try:
            if self.chess_board.player_turn != "black":
                logger.debug("Not AI's turn yet (AI plays as black)")
                return

        except Exception as e:
            logger.error(f"Error in AI move: {e}")
            sentry_sdk.capture_exception(e)

    def closeEvent(self, event):
        """Handle window close event"""
        try:
            # Save game state if it's still in progress
            if not self.chess_board.is_game_over():
                self.end_game()

            # Disconnect from database
            if hasattr(self, "db_connector"):
                self.db_connector._disconnect()

            event.accept()
        except Exception as e:
            logger.error(f"Error during window close: {e}")
            sentry_sdk.capture_exception(e)
            event.accept()


# Initialize logging when the module is imported
configure_logging()

if __name__ == "__main__":
    logger.info("Starting Chess Game Application")
    app = QApplication(sys.argv)
    window = ChessBoardUI()
    window.show()
    sys.exit(app.exec_())
