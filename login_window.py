from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
import logging
from postgres_auth import DBConnector

logger = logging.getLogger(__name__)


class LoginWindow(QWidget):
    login_successful = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.db_connector = DBConnector()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Chess Account")
        self.setFixedSize(400, 450)

        self.setStyleSheet("background-color: rgb(44, 44, 44);")

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(50, 0, 50, 50)

        self.title_label = QLabel()
        queen_pixmap = QPixmap("media/white/Queen.svg")
        scaled_pixmap = queen_pixmap.scaled(
            100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.title_label.setPixmap(scaled_pixmap)
        self.title_label.setFixedSize(100, 100)
        self.title_label.setStyleSheet(
            """
            margin: 0;
            padding: 0;
            background-color: transparent;
        """
        )
        self.title_label.setAlignment(Qt.AlignCenter)

        queen_container = QVBoxLayout()
        queen_container.setContentsMargins(0, 20, 0, 40)
        queen_container.addWidget(self.title_label)
        queen_container.setAlignment(Qt.AlignCenter)

        layout.addLayout(queen_container)

        form_container = QVBoxLayout()
        form_container.setSpacing(10)

        username_label = QLabel("Username:")
        username_label.setStyleSheet(
            "color: white; font-weight: bold; margin-top: 10px;"
        )
        self.username_input = QLineEdit()
        self.username_input.setStyleSheet(
            "background-color: white; color: black; padding: 8px; border-radius: 4px;"
        )

        password_label = QLabel("Password:")
        password_label.setStyleSheet("color: white; font-weight: bold;")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet(
            "background-color: white; color: black; padding: 8px; border-radius: 4px;"
        )

        self.action_button = QPushButton("Sign Up")
        self.action_button.setFixedHeight(80)
        self.action_button.setStyleSheet(
            """
            QPushButton {
                background-color: rgb(64, 144, 78);
                color: rgb(255, 255, 255);
                padding: 8px;
                border: 2px solid rgb(60, 60, 60);
                border-radius: 8px;
                font-size: 14px;
                margin: 20px 0;
                letter-spacing: 2px;
            }
            QPushButton:hover {
                background-color: rgb(60, 60, 60);
                border-color: rgb(70, 70, 70);
            }
            QPushButton:pressed {
                background-color: rgb(40, 40, 40);
                border-color: rgb(50, 50, 50);
            }
        """
        )
        self.action_button.clicked.connect(self.handle_action)

        # Toggle text
        self.toggle_text = QLabel("Already have an account? <u>Sign In</u>")
        self.toggle_text.setStyleSheet(
            """
            color: #9e9e9e;
            font-size: 12px;
            margin-top: 10px;
        """
        )
        self.toggle_text.setAlignment(Qt.AlignCenter)
        self.toggle_text.mousePressEvent = self.toggle_mode

        # Add widgets to layout
        form_container.addWidget(username_label)
        form_container.addWidget(self.username_input)
        form_container.addWidget(password_label)
        form_container.addWidget(self.password_input)
        form_container.addWidget(self.action_button)
        form_container.addWidget(self.toggle_text)

        layout.addLayout(form_container)

        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        # Track current mode
        self.is_signup = True

    def toggle_mode(self, event):
        """Toggle between signup and signin modes"""
        self.is_signup = not self.is_signup
        if self.is_signup:
            self.action_button.setText("Sign Up")
            self.toggle_text.setText("Already have an account? <u>Sign In</u>")
        else:
            self.action_button.setText("Sign In")
            self.toggle_text.setText("Don't have an account? <u>Sign Up</u>")

    def handle_action(self):
        """Handle either signup or signin based on current mode"""
        username = self.username_input.text()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(
                self, "Error", "Please enter both username and password"
            )
            return

        try:
            if self.is_signup:
                # Check if user exists using verify_user with the provided password
                if self.db_connector.verify_user(username, password):
                    QMessageBox.warning(self, "Error", "Username already exists")
                    return

                # Create new user
                self.db_connector.insert_user(username, password)
                logger.info(f"New account created for user: {username}")
                self.login_successful.emit(username)
                self.close()
            else:
                # Verify existing user
                if self.db_connector.verify_user(username, password):
                    logger.info(f"User {username} logged in successfully")
                    self.login_successful.emit(username)
                    self.close()
                else:
                    QMessageBox.warning(self, "Error", "Invalid username or password")
        except Exception as e:
            logger.error(f"Database error: {e}")
            QMessageBox.critical(self, "Error", "Database connection error")

    def closeEvent(self, event):
        """Clean up database connection on window close"""
        if hasattr(self, "db_connector"):
            self.db_connector._disconnect()
        event.accept()
