import unittest
import configparser

from PyQt5.QtWidgets import QApplication
from gui import ChessBoardUI
from db_connector import DBConnector
from os import remove

class TestChessBoardUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication([])

    def setUp(self):
        self.ui = ChessBoardUI()
        self.db_connector = DBConnector('test_chess.db')
        self.db_connector.create_users_table()
        self.db_connector.create_logins_table()
        self.db_connector.insert_user('test_user', 'test_password')

    def tearDown(self):
        self.db_connector._disconnect()
        remove("test_chess.db")

    def test_initialization(self):
        self.assertIsNotNone(self.ui.move_count_label)
        self.assertIsNotNone(self.ui.clock_label)
        self.assertIsNotNone(self.ui.material_count_label)
        self.assertIsNotNone(self.ui.player_to_move_label)
        self.assertIsNotNone(self.ui.grid_layout)
        self.assertIsNotNone(self.ui.chess_board)

    def test_login_valid(self):
        self.ui.username_input.setText('test_user')
        self.ui.password_input.setText('test_password')
        self.ui.handle_login()
        self.assertTrue(self.ui.login_widget.isVisible())

    def test_login_invalid(self):
        self.ui.username_input.setText('invalid_user')
        self.ui.password_input.setText('invalid_password')
        self.ui.handle_login()
        self.assertTrue(self.ui.login_widget.isVisible())

    def test_ui_updates_on_move(self):
        self.ui.chess_board.move_piece(1, 0, 2, 0)  # Move white pawn from (1, 0) to (2, 0)
        self.ui.move_piece(1, 0, 2, 0)
        self.assertEqual(self.ui.move_count_label.text(), "Move count: 0")
        self.assertEqual(self.ui.player_to_move_label.text(), "White to move")

    def test_parse_ini(self):
        # Create a sample ini file
        with open("test_theme.ini", "w") as f:
            f.write("[light_squares]\ncolour = #f0d9b5\n")
            f.write("[dark_squares]\ncolour = #b58863\n")

        expected_result = {
            "light_squares": {"colour": "#f0d9b5"},
            "dark_squares": {"colour": "#b58863"},
        }

        result = self.ui.parse_ini("test_theme.ini")
        self.assertEqual(result, expected_result)

        # Clean up
        remove("test_theme.ini")

if __name__ == "__main__":
    unittest.main()