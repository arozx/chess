import pytest
from pieces import Piece, Rook, Knight, Bishop, Queen, King, Pawn


@pytest.fixture
def empty_board():
    return [[None for _ in range(8)] for _ in range(8)]


def test_piece_selection():
    piece = Piece("white")
    assert not piece.selected
    piece.select()
    assert piece.selected
    piece.deselect()
    assert not piece.selected


def test_rook_moves(empty_board):
    rook = Rook("white")
    empty_board[0][0] = rook
    valid_moves = rook.get_valid_moves(empty_board, 0, 0)
    expected_moves = [(0, i) for i in range(1, 8)] + [(i, 0) for i in range(1, 8)]
    assert set(valid_moves) == set(expected_moves)


def test_knight_moves(empty_board):
    knight = Knight("white")
    empty_board[4][4] = knight
    valid_moves = knight.get_valid_moves(empty_board, 4, 4)
    expected_moves = [(5, 6), (5, 2), (3, 6), (3, 2), (6, 5), (6, 3), (2, 5), (2, 3)]
    assert set(valid_moves) == set(expected_moves)


def test_bishop_moves(empty_board):
    bishop = Bishop("white")
    empty_board[4][4] = bishop
    valid_moves = bishop.get_valid_moves(empty_board, 4, 4)
    expected_moves = [
        (5, 5),
        (6, 6),
        (7, 7),
        (5, 3),
        (6, 2),
        (7, 1),
        (3, 5),
        (2, 6),
        (1, 7),
        (3, 3),
        (2, 2),
        (1, 1),
        (0, 0),
    ]
    assert set(valid_moves) == set(expected_moves)


def test_queen_moves(empty_board):
    queen = Queen("white")
    empty_board[4][4] = queen
    valid_moves = queen.get_valid_moves(empty_board, 4, 4)
    expected_moves = (
        [(4, i) for i in range(8) if i != 4]  # Horizontal moves
        + [(i, 4) for i in range(8) if i != 4]  # Vertical moves
        + [
            (4 + i, 4 + i) for i in range(1, 4) if 0 <= 4 + i < 8
        ]  # Diagonal moves (bottom-right)
        + [
            (4 - i, 4 - i) for i in range(1, 5) if 0 <= 4 - i < 8
        ]  # Diagonal moves (top-left)
        + [
            (4 + i, 4 - i) for i in range(1, 4) if 0 <= 4 + i < 8 and 0 <= 4 - i < 8
        ]  # Diagonal moves (bottom-left)
        + [
            (4 - i, 4 + i) for i in range(1, 5) if 0 <= 4 - i < 8 and 0 <= 4 + i < 8
        ]  # Diagonal moves (top-right)
    )

    assert set(valid_moves) == set(expected_moves)


def test_king_moves(empty_board):
    king = King("white")
    empty_board[4][4] = king
    valid_moves = king.get_valid_moves(empty_board, 4, 4)
    expected_moves = [(4, 5), (4, 3), (5, 4), (3, 4), (5, 5), (5, 3), (3, 5), (3, 3)]
    assert set(valid_moves) == set(expected_moves)


def test_pawn_moves(empty_board):
    pawn = Pawn("white")
    empty_board[1][1] = pawn
    valid_moves = pawn.get_valid_moves(empty_board, 1, 1)
    expected_moves = [(2, 1), (3, 1)]
    assert set(valid_moves) == set(expected_moves)

    pawn.first_move = False
    valid_moves = pawn.get_valid_moves(empty_board, 1, 1)
    expected_moves = [(2, 1)]
    assert set(valid_moves) == set(expected_moves)
