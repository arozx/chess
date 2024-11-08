import unittest
from chess_board_1 import ChessBoard
from pieces import Bishop, King, Knight, Pawn, Queen, Rook
import builtins

class TestChessBoard(unittest.TestCase):
    def setUp(self):
        self.chess_board = ChessBoard()

    def test_initial_setup(self):
        self.assertIsInstance(self.chess_board.board[0][0], Rook)
        self.assertIsInstance(self.chess_board.board[0][1], Knight)
        self.assertIsInstance(self.chess_board.board[0][2], Bishop)
        self.assertIsInstance(self.chess_board.board[0][3], King)
        self.assertIsInstance(self.chess_board.board[0][4], Queen)
        self.assertIsInstance(self.chess_board.board[0][5], Bishop)
        self.assertIsInstance(self.chess_board.board[0][6], Knight)
        self.assertIsInstance(self.chess_board.board[0][7], Rook)
        for i in range(8):
            self.assertIsInstance(self.chess_board.board[1][i], Pawn)
            self.assertIsInstance(self.chess_board.board[6][i], Pawn)
        self.assertIsInstance(self.chess_board.board[7][0], Rook)
        self.assertIsInstance(self.chess_board.board[7][1], Knight)
        self.assertIsInstance(self.chess_board.board[7][2], Bishop)
        self.assertIsInstance(self.chess_board.board[7][3], King)
        self.assertIsInstance(self.chess_board.board[7][4], Queen)
        self.assertIsInstance(self.chess_board.board[7][5], Bishop)
        self.assertIsInstance(self.chess_board.board[7][6], Knight)
        self.assertIsInstance(self.chess_board.board[7][7], Rook)

    def test_load_openings(self):
        openings = self.chess_board.load_openings("./openings/all.tsv")
        self.assertIsInstance(openings, dict)
        self.assertGreater(len(openings), 0)

    def test_get_opening(self):
        self.chess_board.board[0][1] = None  # Clear path for opening move
        self.chess_board.board[1][4] = None  # Clear path for opening move
        self.chess_board.move_piece(1, 4, 3, 4)  # Move white pawn
        self.chess_board.move_piece(6, 3, 4, 3)  # Move black pawn
        opening_name = self.chess_board.get_opening()
        self.assertIsInstance(opening_name, str)
        self.assertEqual(opening_name, "Unknown Opening")

    def test_get_all_valid_moves(self):
        valid_moves = self.chess_board.get_all_valid_moves()
        self.assertGreater(len(valid_moves), 0)

    def test_board_array_to_fen(self):
        fen = self.chess_board.board_array_to_fen()
        self.assertIsInstance(fen, str)
        self.assertGreater(len(fen), 0)

    def test_get_material_count(self):
        white_material = self.chess_board.get_material_count("white")
        black_material = self.chess_board.get_material_count("black")
        self.assertIsInstance(white_material, int)
        self.assertIsInstance(black_material, int)

    def test_move_piece(self):
        self.assertTrue(self.chess_board.move_piece(1, 0, 2, 0))  # Move white pawn
        self.assertFalse(self.chess_board.move_piece(1, 0, 3, 0))  # Invalid move

    def test_enpesaunt(self):
        self.chess_board.move_piece(1, 4, 3, 4)  # Move white pawn
        self.chess_board.move_piece(6, 3, 4, 3)  # Move black pawn
        self.assertFalse(self.chess_board.enpesaunt(3, 4, "white"))

    def test_castling(self):
        self.chess_board.board[0][1] = None  # Clear path for castling
        self.chess_board.board[0][2] = None
        self.chess_board.board[0][3] = King("white")
        self.chess_board.board[0][0] = Rook("white")
        self.chess_board.board[0][4] = None
        self.assertEqual(self.chess_board.castling(self.chess_board.board, "white"), "queenside")

    def test_are_you_in_check(self):
        self.assertEqual(self.chess_board.are_you_in_check("white"), 0)
        self.chess_board.board[1][4] = None  # Clear path for check
        self.chess_board.board[6][4] = Queen("black")
        self.assertEqual(self.chess_board.are_you_in_check("white"), 0)

    def test_game_over(self):
        self.assertFalse(self.chess_board.game_over())
        self.chess_board.board[1][4] = None  # Clear path for checkmate
        self.chess_board.board[6][4] = Queen("black")
        self.chess_board.board[6][5] = Queen("black")
        self.assertFalse(self.chess_board.game_over())

    def test_pawn_promotion(self):
        self.chess_board.board[6][0] = None
        self.chess_board.board[7][0] = None
        self.chess_board.board[7][0] = Pawn("white")  # make white pawn
        self.chess_board.promote_pawn(7, 0, Queen)
        self.assertIsInstance(self.chess_board.board[7][0], Queen)


if __name__ == "__main__":
    unittest.main()