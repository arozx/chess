import copy


class GameState:
    """
    Encapsulates a chess game state with board and player turn
    """

    def __init__(self, board, player_turn="white"):
        self.board = board
        self.player_turn = player_turn

    def clone(self):
        """Create a deep copy of the game state"""
        return GameState(copy.deepcopy(self.board), self.player_turn)

    def __eq__(self, other):
        """Compare two game states for equality"""
        if not isinstance(other, GameState):
            return False

        # Compare boards
        if len(self.board) != len(other.board):
            return False

        for i in range(len(self.board)):
            if len(self.board[i]) != len(other.board[i]):
                return False

            for j in range(len(self.board[i])):
                # Compare pieces
                self_piece = self.board[i][j]
                other_piece = other.board[i][j]

                # If both are None, they're equal
                if self_piece is None and other_piece is None:
                    continue

                # If one is None but the other isn't, they're not equal
                if (self_piece is None) != (other_piece is None):
                    return False

                # Compare piece types and colors
                if (
                    self_piece.__class__.__name__ != other_piece.__class__.__name__
                    or self_piece.colour != other_piece.colour
                ):
                    return False

        # Compare player turns
        return self.player_turn == other.player_turn

    def __hash__(self):
        """Hash function for using GameState as dictionary key"""
        # Create a simple representation of the board for hashing
        board_repr = ""
        for row in self.board:
            for piece in row:
                if piece is None:
                    board_repr += "."
                else:
                    board_repr += f"{piece.__class__.__name__[0]}{piece.colour[0]}"

        return hash(board_repr + self.player_turn)

    def __str__(self):
        """String representation for debugging"""
        piece_map = {
            "white": {
                "Pawn": "P",
                "Rook": "R",
                "Knight": "N",
                "Bishop": "B",
                "Queen": "Q",
                "King": "K",
            },
            "black": {
                "Pawn": "p",
                "Rook": "r",
                "Knight": "n",
                "Bishop": "b",
                "Queen": "q",
                "King": "k",
            },
        }

        board_str = f"Player turn: {self.player_turn}\n"
        for row_idx, row in enumerate(self.board):
            row_str = f"{row_idx} "
            for piece in row:
                if piece is None:
                    row_str += "."
                else:
                    piece_type = piece.__class__.__name__
                    color = piece.colour
                    row_str += piece_map[color][piece_type]
                row_str += " "
            board_str += row_str + "\n"
        board_str += "  0 1 2 3 4 5 6 7"
        return board_str

    @classmethod
    def from_node_or_state(cls, obj):
        """Factory method to ensure we always get a GameState"""
        if isinstance(obj, cls):
            return obj
        if hasattr(obj, "state") and isinstance(obj.state, cls):
            return obj.state
        if hasattr(obj, "board"):
            return cls(obj.board, getattr(obj, "player_turn", "white"))
        # Assume it's a raw board
        return cls(obj, "white")
