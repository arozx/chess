from logging_config import get_logger

# Get logger
logger = get_logger(__name__)

def eval_board(board, player_colour, score_normalised=False):
    """
    Evaluate the board from the perspective of the given player color
    Returns a score (positive is better for the player)
    """
    try:
        # Safety check - ensure board is valid
        if not board or len(board) != 8:
            logger.warning("Invalid board structure in eval_board")
            return 0

        # Piece values
        piece_values = {
            "Pawn": 100,
            "Knight": 320,
            "Bishop": 330,
            "Rook": 500,
            "Queen": 900,
            "King": 20000,
        }

        # Position bonuses for each piece type
        pawn_bonus = [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [5, 10, 10, -20, -20, 10, 10, 5],
            [5, -5, -10, 0, 0, -10, -5, 5],
            [0, 0, 0, 20, 20, 0, 0, 0],
            [5, 5, 10, 25, 25, 10, 5, 5],
            [10, 10, 20, 30, 30, 20, 10, 10],
            [50, 50, 50, 50, 50, 50, 50, 50],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ]

        knight_bonus = [
            [-50, -40, -30, -30, -30, -30, -40, -50],
            [-40, -20, 0, 0, 0, 0, -20, -40],
            [-30, 0, 10, 15, 15, 10, 0, -30],
            [-30, 5, 15, 20, 20, 15, 5, -30],
            [-30, 0, 15, 20, 20, 15, 0, -30],
            [-30, 5, 10, 15, 15, 10, 5, -30],
            [-40, -20, 0, 5, 5, 0, -20, -40],
            [-50, -40, -30, -30, -30, -30, -40, -50],
        ]

        bishop_bonus = [
            [-20, -10, -10, -10, -10, -10, -10, -20],
            [-10, 0, 0, 0, 0, 0, 0, -10],
            [-10, 0, 5, 10, 10, 5, 0, -10],
            [-10, 5, 5, 10, 10, 5, 5, -10],
            [-10, 0, 10, 10, 10, 10, 0, -10],
            [-10, 10, 10, 10, 10, 10, 10, -10],
            [-10, 5, 0, 0, 0, 0, 5, -10],
            [-20, -10, -10, -10, -10, -10, -10, -20],
        ]

        rook_bonus = [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [5, 10, 10, 10, 10, 10, 10, 5],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [0, 0, 0, 5, 5, 0, 0, 0],
        ]

        queen_bonus = [
            [-20, -10, -10, -5, -5, -10, -10, -20],
            [-10, 0, 0, 0, 0, 0, 0, -10],
            [-10, 0, 5, 5, 5, 5, 0, -10],
            [-5, 0, 5, 5, 5, 5, 0, -5],
            [0, 0, 5, 5, 5, 5, 0, -5],
            [-10, 5, 5, 5, 5, 5, 0, -10],
            [-10, 0, 5, 0, 0, 0, 0, -10],
            [-20, -10, -10, -5, -5, -10, -10, -20],
        ]

        king_bonus = [
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-20, -30, -30, -40, -40, -30, -30, -20],
            [-10, -20, -20, -20, -20, -20, -20, -10],
            [20, 20, 0, 0, 0, 0, 20, 20],
            [20, 30, 10, 0, 0, 10, 30, 20],
        ]

        # Development bonus for minor pieces
        development_bonus = 10  # Points for developing minor pieces
        center_control_bonus = 15  # Points for controlling center squares

        white_score = 0
        black_score = 0

        # Count material and add position bonuses
        for i in range(8):
            for j in range(8):
                piece = board[i][j]
                if piece:
                    piece_type = piece.__class__.__name__
                    base_value = piece_values.get(piece_type, 0)
                    position_bonus = 0

                    # Position bonus based on piece type
                    if piece_type == "Pawn":
                        position_bonus = pawn_bonus[i][j]
                    elif piece_type == "Knight":
                        position_bonus = knight_bonus[i][j]
                        # Development bonus for knights
                        if piece.colour == "white" and i > 0:
                            position_bonus += development_bonus
                        elif piece.colour == "black" and i < 7:
                            position_bonus += development_bonus
                    elif piece_type == "Bishop":
                        position_bonus = bishop_bonus[i][j]
                        # Development bonus for bishops
                        if piece.colour == "white" and i > 0:
                            position_bonus += development_bonus
                        elif piece.colour == "black" and i < 7:
                            position_bonus += development_bonus
                    elif piece_type == "Rook":
                        position_bonus = rook_bonus[i][j]
                    elif piece_type == "Queen":
                        position_bonus = queen_bonus[i][j]
                    elif piece_type == "King":
                        position_bonus = king_bonus[i][j]

                    # Center control bonus
                    if 2 <= i <= 5 and 2 <= j <= 5:
                        position_bonus += center_control_bonus

                    # Add to appropriate score
                    if piece.colour == "white":
                        white_score += base_value + position_bonus
                    else:
                        black_score += base_value + position_bonus

        # Calculate final score based on player perspective
        score = (
            white_score - black_score
            if player_colour == "white"
            else black_score - white_score
        )

        # Normalize if requested
        if score_normalised:
            # Normalize to range [-1, 1] based on maximum possible score
            max_possible_score = 40000  # Approximation of maximum score
            return score / max_possible_score

        return float(score)

    except Exception as e:
        logger.error(f"Error in eval_board: {e}")
        return 0  # Return neutral score when error occurs
