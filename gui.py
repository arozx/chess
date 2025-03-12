import configparser
import time
import sys
import traceback
from logging_config import configure_logging, get_logger

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
from db_connector import SQLiteDBConnector
from mcts import MCTS

# Configure logging
logger = get_logger(__name__)

class ChessPiece(QLabel):
    """
    Creates a QLabel widget to display a chess piece
    """
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


class ChessBoardUI(QMainWindow):
    """
    Main window for the chess game
    """
    def __init__(self):
        super().__init__()
        logger.info("Initializing Chess Game UI")
        self.setWindowTitle("Chess Game")
        self.setGeometry(100, 100, 900, 600)

        # Database setup
        self.db_connector = DBConnector()
        self.db_connector.create_users_table()
        self.db_connector.create_logins_table()

        # Open SQLite database
        self.sqlite_connector = SQLiteDBConnector("chess_game.db")
        self.sqlite_connector.create_games_table()
        self.current_game_id = None
        self.player1 = "White"
        self.player2 = "Black"

        # Initialize variables
        self.chess_board = ChessBoard()
        self.selected_piece = None
        self.selected_pos = None

        # Main widget
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        # Labels
        self.move_count_label = QLabel("Move count: 0")
        self.clock_label = QLabel("Elapsed time: 0.00 seconds")
        self.material_count_label = QLabel("Material count: 0")
        self.player_to_move_label = QLabel("White to move")
        self.opening_label = QLabel("Opening: Queen's Gambit")

        # Move history labels
        self.move_history_labels = [QLabel() for _ in range(10)]

        # Export button
        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self.export)

        # Create login UI first
        self.init_login_ui()
        logger.info("Chess Game UI initialized")

    def init_login_ui(self):
        """
        Initialize the login UI
        """
        self.login_widget = QWidget(self)
        login_layout = QVBoxLayout(self.login_widget)

        # Login fields
        self.username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        self.password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        # Login button
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.handle_login)

        # Add widgets to layout
        login_layout.addWidget(self.username_label)
        login_layout.addWidget(self.username_input)
        login_layout.addWidget(self.password_label)
        login_layout.addWidget(self.password_input)
        login_layout.addWidget(self.login_button)

        # Set the login widget as central
        self.setCentralWidget(self.login_widget)

    def export(self):
        """
        Exports the users game
        """
        self.chess_board.board_array_to_pgn()

    def handle_login(self):
        """
        Handle user login
        """
        username = self.username_input.text()
        password = self.password_input.text()
        logger.info(f"Login attempt: {username}")

        if self.db_connector.verify_user(username, password):
            logger.info(f"User {username} logged in successfully")
            self.db_connector.insert_login_attempt(username, time.time())
            self.init_main_ui()  # Switch to the main UI
        else:
            logger.warning(f"Invalid login attempt for user {username}")
            QMessageBox.warning(self, "Login Failed", "Invalid username or password")

    def init_main_ui(self):
        """
        Initialize the main game UI
        """
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
        """
        Calls actions based on button click events
        """
        widget = self.grid_layout.itemAtPosition(row, col).widget()
        if widget.layout() and isinstance(
            widget.layout().itemAt(0).widget(), ChessPiece
        ):
            piece = widget.layout().itemAt(0).widget()
            piece_obj = self.chess_board.board[row][col]
            if piece_obj and piece_obj.colour != self.chess_board.player_turn:
                logger.warning(f"It's {self.chess_board.player_turn}'s turn")
                return
            if self.selected_piece:
                self.move_piece(target_row=row, target_col=col)
            else:
                self.selected_piece = piece
                self.selected_pos = (row, col)
                logger.warning(f"Selected piece at ({row}, {col})")
        elif self.selected_piece:
            self.move_piece(target_row=row, target_col=col)

    def move_piece(
        self, source_row=None, source_col=None, target_row=None, target_col=None
    ):
        """
        Move a piece on the chessboard
        """
        if source_row is None or source_col is None:
            source_row, source_col = self.selected_pos

        if self.chess_board.move_piece(source_row, source_col, target_row, target_col):
            # Update GUI
            source_button = self.grid_layout.itemAtPosition(
                source_row, source_col
            ).widget()
            source_button.layout().itemAt(0).widget().deleteLater()

            target_button = self.grid_layout.itemAtPosition(
                target_row, target_col
            ).widget()
            piece = self.chess_board.board[target_row][target_col]
            if piece:
                piece_label = ChessPiece(piece=piece)
                target_button.layout().addWidget(piece_label)

            # Update labels
            self.move_count_label.setText(f"Move count: {self.chess_board.move_count}")
            self.player_to_move_label.setText(
                f"{self.chess_board.player_turn.capitalize()} to move"
            )
            self.update_move_history(source_row, source_col, target_row, target_col)

            # update opening
            self.opening_label.setText(f"Opening: {self.chess_board.get_opening()}")

            # If it's AI's turn, let AI move
            if self.chess_board.player_turn != "white":  # Assuming AI is black
                QTimer.singleShot(
                    10, self.ai_move
                )  # Delay AI move for a smooth transition

        self.selected_piece = None
        self.selected_pos = None

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

    def save_move(self):
        """
        Save the move history
        """
        self.sqlite_connector.insert_game(
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

    def ai_move(self):
        """
        Get best move using MCTS for the AI (black player)
        """
        from chess_game_adapter import ChessGameAdapter

        # Make sure we're handling black's turn
        if self.chess_board.player_turn != "black":
            logger.debug("Not AI's turn yet (AI plays as black)")
            return

        # Create a game adapter for MCTS
        game_adapter = ChessGameAdapter(self.chess_board)

        # Print info about the current board state
        logger.info(
            f"AI (black) is thinking... Current player turn: {self.chess_board.player_turn}"
        )

        # Debug the board layout
        board_representation = []
        for row_idx, row in enumerate(self.chess_board.board):
            row_str = ""
            for col_idx, piece in enumerate(row):
                if piece is None:
                    row_str += ". "
                else:
                    symbol = (
                        piece.__class__.__name__[0].lower()
                        if piece.colour == "black"
                        else piece.__class__.__name__[0].upper()
                    )
                    row_str += symbol + " "
            board_representation.append(f"{7 - row_idx} {row_str}")

        logger.debug("Current board state:\n" + "\n".join(board_representation))
        logger.debug("  a b c d e f g h")

        # Make sure player turn is black for AI
        self.chess_board.player_turn = "black"

        # Run MCTS with debug output
        mcts = MCTS(
            game_adapter,
            iterations=1000,
            is_white=False,  # AI is always black
            time_limit=5,  # 5 seconds
        )

        try:
            # Run MCTS to get the best move
            best_move = mcts.run()
            if best_move:
                source_pos, dest_pos = best_move
                source_row, source_col = source_pos
                target_row, target_col = dest_pos

                logger.info(
                    f"AI found move: ({source_row}, {source_col}) -> ({target_row}, {target_col})"
                )

                # Validate the move before applying it
                if (
                    0 <= source_row < 8
                    and 0 <= source_col < 8
                    and 0 <= target_row < 8
                    and 0 <= target_col < 8
                ):
                    # Check if there's a piece at the source position
                    piece = self.chess_board.board[source_row][source_col]
                    if piece is None:
                        logger.warning(
                            f"No piece found at ({source_row}, {source_col})"
                        )
                    elif piece.colour != "black":
                        logger.warning(
                            f"Piece at ({source_row}, {source_col}) is not black: {piece.colour}"
                        )
                    else:
                        # Check if the move is in the list of valid moves for this piece
                        valid_moves = piece.get_valid_moves(
                            self.chess_board.board, source_row, source_col
                        )
                        if (target_row, target_col) in valid_moves:
                            logger.info("Move is valid! Applying...")
                            # Apply the move directly using the chess_board's move_piece method
                            result = self.chess_board.move_piece(
                                source_row, source_col, target_row, target_col
                            )

                            if result:
                                logger.info("Move applied successfully")
                                # Update GUI to reflect the move
                                self.update_gui_after_move(
                                    source_row, source_col, target_row, target_col
                                )
                            else:
                                logger.warning("Chess board rejected the move")
                        else:
                            logger.warning(f"Move is not in valid moves: {valid_moves}")
                else:
                    logger.warning("Move coordinates are out of bounds")
            else:
                logger.warning("No valid moves found for AI (black)")
        except Exception as e:
            logger.error(f"Error during AI move: {e}")
            logger.debug(traceback.format_exc())

    def update_gui_after_move(self, source_row, source_col, target_row, target_col):
        """Update GUI after an AI move"""
        # Update GUI
        source_button = self.grid_layout.itemAtPosition(source_row, source_col).widget()
        if source_button.layout().count() > 0:
            source_button.layout().itemAt(0).widget().deleteLater()

        target_button = self.grid_layout.itemAtPosition(target_row, target_col).widget()
        piece = self.chess_board.board[target_row][target_col]
        if piece:
            piece_label = ChessPiece(piece=piece)
            # Clear any existing widgets in the target button
            while target_button.layout().count():
                item = target_button.layout().takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            target_button.layout().addWidget(piece_label)

        # Update labels
        self.move_count_label.setText(f"Move count: {self.chess_board.move_count}")
        self.player_to_move_label.setText(
            f"{self.chess_board.player_turn.capitalize()} to move"
        )
        self.update_move_history(source_row, source_col, target_row, target_col)

        # Update opening
        self.opening_label.setText(f"Opening: {self.chess_board.get_opening()}")

# Initialize logging when the module is imported
configure_logging()

if __name__ == "__main__":
    logger.info("Starting Chess Game Application")
    app = QApplication(sys.argv)
    window = ChessBoardUI()
    window.show()
    sys.exit(app.exec_())
