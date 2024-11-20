import unittest
from unittest.mock import patch, MagicMock
from online.network_client import ChessClient


class TestChessClient(unittest.TestCase):
    @patch("online.network_client.NetworkedChessBoard")
    @patch("online.network_client.NetworkedChessBoardUI")
    def setUp(self, mock_networked_chess_board_ui, mock_networked_chess_board):
        self.mock_chess_board = mock_networked_chess_board.return_value
        self.mock_chess_board_ui = mock_networked_chess_board_ui.return_value
        self.client = ChessClient()

    def test_initialization(self):
        self.assertIsInstance(self.client.chess_board, MagicMock)
        self.assertIsInstance(self.client.chess_board_ui, MagicMock)
        self.client.chess_board.socket.settimeout.assert_called_with(5)

    @patch("online.network_client.pickle.loads")
    def test_receive_data(self, mock_pickle_loads):
        mock_data = MagicMock()
        mock_move = ("e2", "e4")
        mock_pickle_loads.return_value = mock_move
        self.client.chess_board.socket.recv = MagicMock(side_effect=[mock_data, b""])

        with patch.object(
            self.client.chess_board, "move_piece"
        ) as mock_move_piece, patch.object(
            self.client.chess_board_ui, "update_ui"
        ) as mock_update_ui:
            self.client.receive_data()
            mock_move_piece.assert_called_with(*mock_move)
            mock_update_ui.assert_called()

    def test_teardown(self):
        self.client.teardown()
        self.client.chess_board.socket.close.assert_called()
        if hasattr(self.client.chess_board, "receive_thread"):
            self.client.chess_board.receive_thread.join.assert_called()
        self.client.chess_board_ui.close.assert_called()


if __name__ == "__main__":
    unittest.main()


if __name__ == "__main__":
    unittest.main()
