from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
)
from PyQt5.QtCore import pyqtSignal
from postgres_auth import DBConnector
import logging

logger = logging.getLogger(__name__)


class LoginWindow(QWidget):
    login_successful = pyqtSignal(str)  # Signal to emit when login is successful

    def __init__(self):
        super().__init__()
        self.db = DBConnector()
        self.init_ui()

    def init_ui(self):
        # Create layout
        layout = QVBoxLayout()

        # Username field
        username_layout = QHBoxLayout()
        username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)

        # Password field
        password_layout = QHBoxLayout()
        password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)

        # Buttons
        button_layout = QHBoxLayout()
        self.login_button = QPushButton("Login")
        self.register_button = QPushButton("Register")
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.register_button)

        # Add all layouts to main layout
        layout.addLayout(username_layout)
        layout.addLayout(password_layout)
        layout.addLayout(button_layout)

        # Set window properties
        self.setLayout(layout)
        self.setWindowTitle("Chess Login")
        self.setGeometry(300, 300, 300, 150)

        # Connect buttons to functions
        self.login_button.clicked.connect(self.handle_login)
        self.register_button.clicked.connect(self.handle_register)

        # Create tables if they don't exist
        self.db.create_users_table()
        self.db.create_logins_table()

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Please fill in all fields")
            return

        try:
            if self.db.verify_user(username, password):
                # Record login time
                import time

                self.db.insert_login_attempt(username, time.time())

                # Emit signal with username
                self.login_successful.emit(username)

                # Close login window
                self.close()
            else:
                QMessageBox.warning(self, "Error", "Invalid username or password")
        except Exception as e:
            logger.error(f"Login error: {e}")
            QMessageBox.critical(self, "Error", "An error occurred during login")

    def handle_register(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Please fill in all fields")
            return

        try:
            self.db.insert_user(username, password)
            QMessageBox.information(
                self, "Success", "Registration successful! You can now login."
            )
        except Exception as e:
            logger.error(f"Registration error: {e}")
            QMessageBox.critical(
                self, "Error", "Username already exists or an error occurred"
            )
