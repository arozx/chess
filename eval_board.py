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

        # Position bonuses for each piece type (simplified)
        pawn_bonus = [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [50, 50, 50, 50, 50, 50, 50, 50],
            [10, 10, 20, 30, 30, 20, 10, 10],
            [5, 5, 10, 25, 25, 10, 5, 5],
            [0, 0, 0, 20, 20, 0, 0, 0],
            [5, -5, -10, 0, 0, -10, -5, 5],
            [5, 10, 10, -20, -20, 10, 10, 5],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ]

        # Similar bonus tables for other pieces would go here
        # (For brevity, we're only implementing pawn bonuses)

        white_score = 0
        black_score = 0

        # Count material and add position bonuses
        for i in range(8):
            for j in range(8):
                piece = board[i][j]
                if piece:
                    piece_type = piece.__class__.__name__
                    base_value = piece_values.get(piece_type, 0)

                    # Position bonus based on piece type
                    position_bonus = 0
                    if piece_type == "Pawn":
                        # Use the appropriate row based on color (flip for black)
                        if piece.colour == "white":
                            position_bonus = pawn_bonus[i][j]
                        else:
                            position_bonus = pawn_bonus[7 - i][j]

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

        return score

    except Exception as e:
        logger.error(f"Error in eval_board: {e}")
        return 0  # Return neutral score when error occurs
