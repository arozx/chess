import sys
from PyQt5.QtWidgets import QApplication, QLabel, QGridLayout, QWidget, QPushButton, QVBoxLayout, QLineEdit
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
from chess_board_1 import ChessBoard
import time
from postgres_auth import DBConnector
from mcts import MCTS, Node

class ChessPiece(QLabel):
    def __init__(self, parent=None, piece=None):
        super().__init__(parent)
        self.setFixedSize(60, 60)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: transparent;")
        if piece:
            pixmap = QPixmap(f"media/{piece.colour}/{piece.__class__.__name__.upper()[0:1]}{piece.__class__.__name__.lower()[1::]}.svg")
            scaled_pixmap = pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.setPixmap(scaled_pixmap)

class ChessBoardUI(QWidget):
    def __init__(self):
        super().__init__()
        self.db_connector = DBConnector()
        self.db_connector.create_users_table()
        self.db_connector.create_logins_table()
        self.init_login_ui()

        # Initialize labels
        self.move_count_label = QLabel("Move count: 0")
        self.clock_label = QLabel("Elapsed time: 0.00 seconds")
        self.material_count_label = QLabel("Material count: 0")
        self.player_to_move_label = QLabel("White to move")

        # Initialize grid_layout and other variables
        self.grid_layout = QGridLayout()
        self.chess_board = ChessBoard()
        self.selected_piece = None
        self.selected_pos = None

    def init_login_ui(self):
        self.login_widget = QWidget()
        self.login_layout = QVBoxLayout(self.login_widget)
        
        self.username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        self.password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.handle_login)
        
        self.login_layout.addWidget(self.username_label)
        self.login_layout.addWidget(self.username_input)
        self.login_layout.addWidget(self.password_label)
        self.login_layout.addWidget(self.password_input)
        self.login_layout.addWidget(self.login_button)
        
        self.login_widget.show()

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        if self.db_connector.verify_user(username, password):
            self.db_connector.insert_login_attempt(username, time.time())
            self.login_widget.hide()
            self.show_main_ui()
        else:
            print("Invalid username or password")

    def show_main_ui(self):
        self.init_ui()  # Initialize the main game UI
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.move_count_label)
        self.layout().addWidget(self.clock_label)
        self.layout().addWidget(self.material_count_label)
        self.layout().addWidget(self.player_to_move_label)
        self.layout().addLayout(self.grid_layout)
        self.start_timer()  # Start the timer after login
        self.show()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.move_count_label)
        main_layout.addWidget(self.clock_label)
        main_layout.addWidget(self.material_count_label)  # Add material count label to layout
        main_layout.addLayout(self.grid_layout)

        for row in range(8):
            for col in range(8):
                if (row + col) % 2 == 0:
                    color = "white"
                else:
                    color = "gray"
                button = QPushButton()
                button.setFixedSize(60, 60)
                button.setStyleSheet(f"background-color: {color}; border: none;")  # Remove padding and make flat
                button.setLayout(QVBoxLayout())  # Add layout to center pieces
                button.layout().setAlignment(Qt.AlignCenter)  # Center the layout
                button.clicked.connect(lambda _, r=row, c=col: self.handle_click(r, c))
                self.grid_layout.addWidget(button, row, col)

                piece = self.chess_board.board[row][col]
                if piece:
                    piece_label = ChessPiece(piece=piece)
                    piece_label.setAlignment(Qt.AlignCenter)  # Ensure the piece is centered
                    button.layout().addWidget(piece_label)

    def start_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(10)  # Update every 10ms

    def update_clock(self):
        elapsed_time = time.time() - self.chess_board.start_time
        self.clock_label.setText(f"Elapsed time: {elapsed_time:.2f} seconds")

    def handle_click(self, row, col):
        widget = self.grid_layout.itemAtPosition(row, col).widget()
        if widget.layout() and isinstance(widget.layout().itemAt(0).widget(), ChessPiece):
            piece = widget.layout().itemAt(0).widget()
            piece_obj = self.chess_board.board[row][col]
            if piece_obj and piece_obj.colour != self.chess_board.player_turn:
                print(f"It's {self.chess_board.player_turn}'s turn")
                return
            if self.selected_piece:
                self.move_piece(target_row=row, target_col=col)
            else:
                self.selected_piece = piece
                self.selected_pos = (row, col)
                print(f"Selected piece at ({row}, {col})")
        elif self.selected_piece:
            self.move_piece(target_row=row, target_col=col)

    def move_piece(self, source_row=None, source_col=None, target_row=None, target_col=None, is_ai_move=False):
        if source_row is None or source_col is None:
            source_row, source_col = self.selected_pos

        captured_piece = self.chess_board.board[target_row][target_col]

        if self.chess_board.move_piece(source_row, source_col, target_row, target_col):
            # Update GUI buttons
            source_button = self.grid_layout.itemAtPosition(source_row, source_col).widget()
            source_button.layout().itemAt(0).widget().deleteLater()

            target_button = self.grid_layout.itemAtPosition(target_row, target_col).widget()
            piece = self.chess_board.board[target_row][target_col]
            if piece:
                piece_label = ChessPiece(piece=piece)
                target_button.layout().addWidget(piece_label)

            print(f"Moved from ({source_row}, {source_col}) to ({target_row}, {target_col})")
            self.move_count_label.setText(f"Move count: {self.chess_board.move_count}")

            self.player_to_move_label.setText(f"{self.chess_board.player_turn[0:1].upper()}{self.chess_board.player_turn[1::]} to move")
            if captured_piece:
                self.update_material_count()

            # Check if it's AI's turn
            if self.chess_board.player_turn != 'white' and not is_ai_move:
                # Delay AI move to update GUI first
                QTimer.singleShot(100, self.ai_move)  # Delay of 100 milliseconds
        else:
            print("Move invalid")

        self.selected_piece = None
        self.selected_pos = None

    def ai_move(self):
        # Create a root node with current board state
        root_node = Node(self.chess_board.board)
        # Initialize MCTS with root node
        mcts = MCTS(root_node, iterations=1000, is_white=(self.chess_board.player_turn == 'white'))
        # Run MCTS
        mcts.run()
        # Get best move from MCTS
        best_move = mcts.best_move()
        # Extract source and destination squares
        (source_pos, dest_pos) = best_move
        source_row, source_col = source_pos
        target_row, target_col = dest_pos
        # Move the piece
        self.move_piece(
            source_row=source_row,
            source_col=source_col,
            target_row=target_row,
            target_col=target_col,
            is_ai_move=True  # Indicate that this move is made by the AI
        )

    def update_material_count(self):
        material_count = self.chess_board.get_material_count()
        self.material_count_label.setText(f"Material count: {material_count}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChessBoardUI()
    window.show()
    sys.exit(app.exec_())
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChessBoardUI()
    window.show()
    window = ChessBoardUI()
    sys.exit(app.exec_())
    window.show()
    sys.exit(app.exec_())