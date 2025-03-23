import traceback
from logging_config import get_logger
from eval_board import eval_board

# Get logger
logger = get_logger(__name__)


class ChessGameAdapter:
    """
    Adapts the ChessBoard class to work with the MCTS algorithm.
    Provides the interface expected by MCTS: is_terminal, get_legal_moves, apply_move, etc.
    """

    def __init__(self, chess_board):
        self.chess_board = chess_board
        # Debug current board layout to understand piece positions
        self.debug_board_layout(self.chess_board.board)

    def debug_board_layout(self, board):
        """Print the current board layout to understand piece positions"""
        logger.info("Current board layout:")
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

        board_representation = []
        for row_idx, row in enumerate(board):
            row_str = f"{row_idx} "
            for piece in row:
                if piece is None:
                    row_str += "."
                else:
                    piece_type = piece.__class__.__name__
                    color = piece.colour
                    row_str += piece_map[color][piece_type]
                row_str += " "
            board_representation.append(row_str)

        # Log the entire board at once
        logger.info("\n" + "\n".join(board_representation))
        logger.info("  0 1 2 3 4 5 6 7")
        logger.info(f"Current player turn: {self.chess_board.player_turn}")

    def is_terminal(self, board):
        """Check if the state represents a terminal state"""
        return board.game_over()

    def get_legal_moves(self, board):
        """Get all legal moves from the current state"""
        try:
            all_moves = []
            # Find king position first
            king_position = None
            for i in range(8):
                for j in range(8):
                    piece = board.board[i][j]
                    if (
                        piece
                        and piece.__class__.__name__ == "King"
                        and piece.colour == board.player_turn
                    ):
                        king_position = (i, j)
                        break
                if king_position:
                    break

            if not king_position:
                logger.warning(f"No {board.player_turn} king found on the board")
                return []

            # Check if we're currently in check
            current_check_status = board.are_you_in_check(board.player_turn)
            logger.debug(f"Current check status: {current_check_status}")

            # Get all potential moves
            for x in range(8):
                for y in range(8):
                    piece = board.board[x][y]
                    if piece and piece.colour == board.player_turn:
                        # Get valid moves using the piece's method directly
                        valid_moves = piece.get_valid_moves(board.board, x, y)
                        for move in valid_moves:
                            # Create a temporary board to test the move
                            temp_board = board.clone()
                            if temp_board.move_piece(x, y, move[0], move[1]):
                                # If we're in check, only add moves that get us out of check
                                if current_check_status > 0:
                                    if (
                                        temp_board.are_you_in_check(board.player_turn)
                                        == 0
                                    ):
                                        all_moves.append(((x, y), move))
                                        logger.debug(
                                            f"Found escape move from check: ({x},{y}) to {move}"
                                        )
                                else:
                                    # If we're not in check, add moves that don't put us in check
                                    if (
                                        temp_board.are_you_in_check(board.player_turn)
                                        == 0
                                    ):
                                        all_moves.append(((x, y), move))

            if not all_moves:
                if current_check_status > 0:
                    logger.warning(
                        "No legal moves found to escape check - possible checkmate"
                    )
                else:
                    logger.warning("No legal moves found - possible stalemate")

            # Prioritize moves that capture pieces or control the center
            def move_score(move):
                from_pos, to_pos = move
                to_x, to_y = to_pos
                # Check if move captures a piece
                target_piece = board.board[to_x][to_y]
                score = 0
                if target_piece:
                    score += target_piece.weight * 10  # Prioritize captures
                # Bonus for controlling center squares
                if 2 <= to_x <= 5 and 2 <= to_y <= 5:
                    score += 5
                return score

            # Sort moves by score, highest first
            all_moves.sort(key=move_score, reverse=True)
            return all_moves

        except Exception as e:
            logger.error(f"Error in get_legal_moves: {e}\n{traceback.format_exc()}")
            return []

    def apply_move(self, board, move):
        """Apply a move to a state and return new state"""
        try:
            new_board = board.clone()
            from_pos, to_pos = move
            if new_board.move_piece(from_pos[0], from_pos[1], to_pos[0], to_pos[1]):
                return new_board
            return None
        except Exception as e:
            logger.error(f"Error applying move: {e}")
            return None

    def get_reward(self, board, is_white):
        """Calculate the reward for the current board state."""
        try:
            # Find king position for the current player
            king_color = "white" if is_white else "black"
            king_position = None
            for i in range(8):
                for j in range(8):
                    piece = board.board[i][j]
                    if (
                        piece
                        and piece.__class__.__name__ == "King"
                        and piece.colour == king_color
                    ):
                        king_position = (i, j)
                        break
                if king_position:
                    break

            if not king_position:
                logger.warning(f"No {king_color} king found on the board")
                return 0.0

            # Check for checkmate using the king's position
            if board.is_checkmate(is_white, king_position):
                return -1.0  # Loss

            # Find opponent's king position
            opponent_king_position = None
            opponent_color = "black" if is_white else "white"
            for i in range(8):
                for j in range(8):
                    piece = board.board[i][j]
                    if (
                        piece
                        and piece.__class__.__name__ == "King"
                        and piece.colour == opponent_color
                    ):
                        opponent_king_position = (i, j)
                        break
                if opponent_king_position:
                    break

            if opponent_king_position and board.is_checkmate(
                not is_white, opponent_king_position
            ):
                return 1.0  # Win

            # Get position evaluation from eval_board
            score = eval_board(
                board.board, "white" if is_white else "black", score_normalised=True
            )

            # Return normalized score between -1 and 1
            return score

        except Exception as e:
            logger.error(f"Error in get_reward: {e}\n{traceback.format_exc()}")
            return 0.0  # Return neutral score on error
