import copy
import traceback
from logging_config import get_logger
from eval_board import eval_board
from game_state import GameState

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

    def is_terminal(self, state_or_node):
        """Check if the state represents a terminal state"""
        state = GameState.from_node_or_state(state_or_node)
        if not isinstance(state, GameState):
            return False

        temp_board = copy.deepcopy(self.chess_board)
        temp_board.board = state.board
        temp_board.player_turn = state.player_turn
        return temp_board.game_over()

    def get_legal_moves(self, state_or_node):
        """Get all legal moves from the current state"""
        # Convert to GameState if needed
        state = GameState.from_node_or_state(state_or_node)

        if not isinstance(state, GameState):
            logger.warning(f"Expected GameState, got {type(state).__name__}")
            return []

        # Copy board configuration
        temp_board = copy.deepcopy(self.chess_board)
        temp_board.board = state.board
        temp_board.player_turn = state.player_turn  # Make sure this is set correctly

        logger.info(f"Finding moves for player: {temp_board.player_turn}")

        # Count pieces by color for debugging
        white_pieces = sum(
            1
            for row in temp_board.board
            for piece in row
            if piece and piece.colour == "white"
        )
        black_pieces = sum(
            1
            for row in temp_board.board
            for piece in row
            if piece and piece.colour == "black"
        )
        logger.debug(f"Pieces on board: {white_pieces} white, {black_pieces} black")

        # Get all valid moves for each piece of the current player's color
        all_moves = []
        for from_x in range(8):
            for from_y in range(8):
                piece = temp_board.board[from_x][from_y]
                # Ensure pieces exist and are of the correct color
                if piece and piece.colour == temp_board.player_turn:
                    try:
                        # Get valid moves for this piece
                        valid_moves = piece.get_valid_moves(
                            temp_board.board, from_x, from_y
                        )
                        # Add moves in the format ((from_x, from_y), (to_x, to_y))
                        piece_moves = [((from_x, from_y), move) for move in valid_moves]
                        all_moves.extend(piece_moves)

                        if valid_moves:
                            logger.info(
                                f"Found {len(valid_moves)} moves for {piece.colour} {piece.__class__.__name__} at ({from_x}, {from_y}): {valid_moves}"
                            )
                    except Exception as e:
                        logger.error(
                            f"Error getting moves for {piece.colour} {piece.__class__.__name__} at ({from_x},{from_y}): {e}"
                        )

        logger.info(f"Found {len(all_moves)} total legal moves for {state.player_turn}")
        return all_moves

    def apply_move(self, state_or_node, move):
        """Apply a move to a state and return new GameState"""
        state = GameState.from_node_or_state(state_or_node)
        if not isinstance(state, GameState):
            logger.warning("Cannot apply move: Input is not a GameState")
            return None

        try:
            new_state = state.clone()
            from_pos, to_pos = move

            # Debug information
            logger.debug(f"Applying move: {from_pos} -> {to_pos}")

            # Validate positions
            if not (0 <= from_pos[0] < 8 and 0 <= from_pos[1] < 8) or not (
                0 <= to_pos[0] < 8 and 0 <= to_pos[1] < 8
            ):
                logger.warning("Move is out of bounds")
                return None

            # Get the piece at the source position
            piece = new_state.board[from_pos[0]][from_pos[1]]
            if not piece:
                logger.warning(f"No piece at source position {from_pos}")
                return None

            # Verify that the piece belongs to the current player
            if piece.colour != new_state.player_turn:
                logger.warning(
                    f"Piece at {from_pos} is {piece.colour} but it's {new_state.player_turn}'s turn"
                )
                return None

            # Verify that the move is valid for this piece
            valid_moves = piece.get_valid_moves(
                new_state.board, from_pos[0], from_pos[1]
            )
            if to_pos not in valid_moves:
                logger.warning(
                    f"Move to {to_pos} is not valid for {piece.__class__.__name__} at {from_pos}"
                )
                return None

            # Apply the move
            logger.info(
                f"Moving {piece.__class__.__name__} from {from_pos} to {to_pos}"
            )
            new_state.board[to_pos[0]][to_pos[1]] = piece
            new_state.board[from_pos[0]][from_pos[1]] = None

            # Switch turns
            new_state.player_turn = "black" if state.player_turn == "white" else "white"

            return new_state

        except Exception as e:
            logger.error(f"Error applying move: {e}")
            logger.debug(traceback.format_exc())
            return None

    def get_reward(self, state_or_node, is_white):
        """Calculate the reward for a terminal state"""
        try:
            state = GameState.from_node_or_state(state_or_node)
            if not isinstance(state, GameState) or not state.board:
                logger.warning(f"Invalid state in get_reward: {type(state).__name__}")
                return 0

            # Validate board structure
            if len(state.board) != 8 or any(len(row) != 8 for row in state.board):
                logger.warning("Invalid board dimensions in get_reward")
                return 0

            temp_board = copy.deepcopy(self.chess_board)
            temp_board.board = state.board
            temp_board.player_turn = state.player_turn

            # Check for checkmate conditions
            try:
                if temp_board.are_you_in_check("black" if is_white else "white") == 2:
                    # Checkmate in favor of the current player
                    return 1.0
                elif temp_board.are_you_in_check("white" if is_white else "black") == 2:
                    # Checkmate against the current player
                    return -1.0
            except Exception as check_error:
                logger.error(f"Error checking for checkmate: {check_error}")
                # Continue to board evaluation if checkmate check fails

            # Use board evaluation for non-terminal or draw states
            try:
                return (
                    eval_board(
                        state.board,
                        "white" if is_white else "black",
                        score_normalised=False,
                    )
                    / 100.0
                )  # Normalize evaluation
            except Exception as eval_error:
                logger.error(f"Error in board evaluation: {eval_error}")
                return 0.0  # Neutral score on error

        except Exception as e:
            logger.error(f"Error in get_reward: {e}")
            return 0.0  # Safe default value
