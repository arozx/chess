import chess
import time
import csv
import copy
import sentry_sdk
from logging_config import get_logger
from performance_monitoring import (
    track_performance,
    measure_operation,
    track_slow_operations,
)
from dotenv import load_dotenv
from chess import pgn

from pieces import Bishop, King, Knight, Pawn, Queen, Rook
import io
import uuid
import os

# Load environment variables
load_dotenv()

# Configure logging
logger = get_logger(__name__)

# Configure Sentry with user identification
def configure_sentry():
    try:
        # Generate a unique user ID if not already stored
        user_id = str(uuid.uuid4())

        # Get Sentry DSN from environment variable
        dsn = os.getenv("SENTRY_DSN")
        if not dsn:
            logger.warning("No Sentry DSN provided. Error tracking will be disabled.")
            return

        # Configure Sentry with user context
        sentry_sdk.init(
            dsn=dsn,
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
            environment=os.getenv("ENVIRONMENT", "development"),
            enable_tracing=True,
        )

        # Set user context
        sentry_sdk.set_user(
            {
                "id": user_id,
                "game_id": f"chess_{int(time.time())}",
            }
        )

        # Set additional tags
        sentry_sdk.set_tag("app_type", "chess_game")
        sentry_sdk.set_tag("platform", os.name)

        logger.info(f"Sentry configured with user ID: {user_id}")
    except Exception as e:
        logger.error(f"Error configuring Sentry: {e}")
        logger.error("Continuing without error tracking")


# Call Sentry configuration
configure_sentry()


class ChessBoard:
    def __init__(self):
        try:
            with measure_operation("init_chess_board", "initialization"):
                logger.info("Initializing ChessBoard")
                self.move_count = 0
                self.player_turn = "white"
                self.material = -1
                self.start_time = time.time()  # Initialize start time
                self.game_id = f"chess_{int(self.start_time)}"

                # Update Sentry context with game information
                sentry_sdk.set_context(
                    "game",
                    {
                        "game_id": self.game_id,
                        "start_time": self.start_time,
                    },
                )

                self.board = [[None for _ in range(8)] for _ in range(8)]

                # Initialize board_cache with the correct size
                self.board_cache = ["|  |" for _ in range(64)]

                # Initialize pieces with performance tracking
                self._initialize_pieces()

                self.openings = self.load_openings("./openings/all.tsv")
                logger.info("ChessBoard initialized")
        except Exception as e:
            logger.error(f"Error initializing chess board: {e}")
            sentry_sdk.capture_exception(e)
            raise

    @track_performance(op="initialization", name="initialize_pieces")
    def _initialize_pieces(self):
        """Initialize chess pieces with performance tracking"""
        # Create white pieces
        self.board[0][0] = Rook("white")
        self.board[0][1] = Knight("white")
        self.board[0][2] = Bishop("white")
        self.board[0][3] = King("white")  # King should be on e1 (0,3)
        self.board[0][4] = Queen("white")  # Queen should be on d1 (0,4)
        self.board[0][5] = Bishop("white")
        self.board[0][6] = Knight("white")
        self.board[0][7] = Rook("white")
        for i in range(8):
            self.board[1][i] = Pawn("white")

        # Create black pieces
        self.board[7][0] = Rook("black")
        self.board[7][1] = Knight("black")
        self.board[7][2] = Bishop("black")
        self.board[7][3] = King("black")  # King should be on e8 (7,3)
        self.board[7][4] = Queen("black")  # Queen should be on d8 (7,4)
        self.board[7][5] = Bishop("black")
        self.board[7][6] = Knight("black")
        self.board[7][7] = Rook("black")
        for i in range(8):
            self.board[6][i] = Pawn("black")

    def load_openings(self, file_path):
        try:
            with sentry_sdk.start_span(
                op="chess.load_openings", description="Loading chess openings"
            ) as span:
                logger.info(f"Loading openings from {file_path}")
                openings = {}
                logger.info(f"path: {file_path}")
                with open(file_path, newline="", encoding="utf-8") as tsvfile:
                    reader = csv.reader(tsvfile, delimiter="\t")
                    for row in reader:
                        if len(row) >= 3:
                            name = row[1]
                            moves = row[2]
                            openings[moves] = name
                return openings
        except Exception as e:
            logger.error(f"Error loading openings: {e}")
            sentry_sdk.capture_exception(e)
            return {}

    def get_opening(self):
        try:
            with sentry_sdk.start_span(
                op="chess.get_opening", description="Get current opening"
            ) as span:
                current_moves = " ".join(self.get_epd())
                for moves, name in self.openings.items():
                    if current_moves.startswith(moves):
                        opening = name
                        logger.debug(f"Current opening: {opening}")
                        return opening
                return "Unknown Opening"
        except Exception as e:
            logger.error(f"Error getting opening: {e}")
            sentry_sdk.capture_exception(e)
            return "Unknown Opening"

    """
    Takes no arguments
    Returns a EPD string
    """

    def get_epd(self):
        try:
            with sentry_sdk.start_span(
                op="chess.get_epd", description="Get EPD notation"
            ) as span:
                board = chess.Board(self.board_array_to_fen())
                epd = board.epd()
                logger.debug(f"EPD: {epd}")
                return epd
        except Exception as e:
            logger.error(f"Error getting EPD: {e}")
            sentry_sdk.capture_exception(e)
            return ""

    """
    Takes no arguments
    Returns an array of moves that are legal
    """

    def get_all_valid_moves(self):
        try:
            with sentry_sdk.start_span(
                op="chess.get_valid_moves", description="Get all valid moves"
            ) as span:
                board = chess.Board(self.board_array_to_fen())
                valid_moves = [move.uci() for move in board.legal_moves]
                logger.debug(f"All valid moves: {valid_moves}")
                return valid_moves
        except Exception as e:
            logger.error(f"Error getting valid moves: {e}")
            sentry_sdk.capture_exception(e)
            return []

    """
    Takes no arguments
    Returns the board as a FEN string
    """

    def board_array_to_fen(self):
        try:
            with sentry_sdk.start_span(
                op="chess.board_to_fen", description="Convert board to FEN"
            ) as span:
                board = chess.Board()
                board.clear_board()
                for rank in range(8):
                    for file in range(8):
                        piece = self.board[rank][file]
                        if piece is not None:
                            board.set_piece_at(
                                chess.square(file, 7 - rank),
                                chess.Piece.from_symbol(piece.symbol),
                            )
                return board.fen()
        except Exception as e:
            logger.error(f"Error converting board to FEN: {e}")
            sentry_sdk.capture_exception(e)
            return ""

    """
    Takes no arguments
    Returns the name of a PGN file containing the current board
    """

    def board_array_to_pgn(self):
        try:
            with sentry_sdk.start_span(
                op="chess.board_to_pgn", description="Convert board to PGN"
            ) as span:
                board = chess.Board(self.board_array_to_fen())
                file_io = io.StringIO()
                exporter = pgn.FileExporter(file_io)
                game = pgn.Game.from_board(board)
                game.accept(exporter)
                pgn_string = pgn.getvalue(self.board_array_to_fen)

                file_name = f"game_{int(time.time())}.pgn"
                with open(file_name, "w") as pgn_file:
                    pgn_file.write(pgn_string)

                logger.info(f"PGN file saved as {file_name}")
                return file_name
        except Exception as e:
            logger.error(f"Error converting board to PGN: {e}")
            sentry_sdk.capture_exception(e)
            return None

    """
    Takes no arguments
    Returns the material as a positive or negative number
    Value is positive for white and negative for black
    """

    def get_material_count(self, colour):
        try:
            with sentry_sdk.start_span(
                op="chess.get_material", description=f"Get material count for {colour}"
            ) as span:
                material = 0
                for x in range(8):
                    for y in range(8):
                        if self.board[x][y] is not None:
                            if self.board[x][y].colour == colour:
                                material += self.board[x][y].weight
                            else:
                                material -= self.board[x][y].weight
                logger.debug(f"Material count for {colour}: {material}")
                return material
        except Exception as e:
            logger.error(f"Error calculating material count: {e}")
            sentry_sdk.capture_exception(e)
            return 0

    """
    takes no arguments
    prints the board as text
    Returns N/A
    ! THIS IS A DEVELOPMENT FUNCTION
    """

    def display_board_as_text(self):
        self.board_cache = []
        for x in range(0, 8):
            for y in range(0, 8):
                if self.board[x][y] is None:
                    self.board_cache.append("|  |")
                else:
                    self.board_cache.append(
                        "|" + self.board[x][y].__class__.__name__[0:2] + "|"
                    )

        for i in range(0, 8):
            logger.debug(self.board_cache[i * 8 : i * 8 + 8])
        logger.debug("Board displayed as text")

    """
    takes no arguments
    Prints the colours of the pieces on the board
    Returns: N/A
    ! THIS IS A DEVELOPMENT FUNCTION
    """

    def display_board_as_colours(self):
        colours = []
        for x in range(0, 8):
            for y in range(0, 8):
                if self.board[x][y] is None:
                    colours.append("|  |")
                else:
                    colours.append("|" + self.board[x][y].colour[0:2] + "|")

        for i in range(0, 8):
            logger.debug(colours[i * 8 : i * 8 + 8])
        logger.debug("Board displayed as colours")

    """
    takes no arguments
    Prints the coordinates of the board
    Returns: N/A
    ! INVERTED TO READ AS X, Y WHEN y then x
    """

    def display_board_as_coordinates(self):
        coordinates = []
        for x in range(0, 8):
            for y in range(0, 8):
                coordinates.append(f"|{x}{y}|")

        for i in range(0, 8):
            logger.debug(coordinates[i * 8 : i * 8 + 8])
        logger.debug("Board displayed as coordinates")

    """
    take a x and y for starting take an x any y for end pos
    updates the board & board_cache
    updates the material & move_count if the move is valid
    ends early and reutrns false if the move causes check, there is no pice at the start or the end pos is not in the valid moves
    returns True if move is valid
    """

    @track_performance(op="en_passant", name="check_en_passant")
    def enpesaunt(self, x, y, colour):
        try:
            if isinstance(self.board[x][y], Pawn):
                direction = 1 if colour == "white" else -1
                if (
                    isinstance(self.board[x][y + 1], Pawn)
                    and self.board[x][y + 1].colour != colour
                    and self.board[x][y + 1].first_move
                    and self.board[x + direction][y + 1] is None
                ):
                    logger.debug(f"pawn on ({x}, {y + 1})")
                    result = True
                    logger.debug(
                        f"En passant check at ({x}, {y}) for {colour}: {result}"
                    )
                    return result
                elif (
                    isinstance(self.board[x][y - 1], Pawn)
                    and self.board[x][y - 1].colour != colour
                    and self.board[x][y - 1].first_move
                    and self.board[x + direction][y - 1] is None
                ):
                    logger.debug(f"pawn on ({x}, {y - 1})")
                    result = True
                    logger.debug(
                        f"En passant check at ({x}, {y}) for {colour}: {result}"
                    )
                    return result
        except IndexError:
            # raised when enpseant is checked for outside the board
            return False
        return False

    """
    Take the board as an argument & player_colour
    returns False if castling is not possible
    returns "kingside" or "queenside"
    """

    @track_performance(op="castling", name="check_castling")
    def castling(self, board, player_colour):
        """Check if castling is possible for the given player"""
        try:
            # Get king position based on color
            king_row = 0 if player_colour == "white" else 7
            king_col = 3  # King's initial column

            # Check if king exists and hasn't moved
            king = board[king_row][king_col]
            if not isinstance(king, King) or not king.first_move:
                return False

            # Check queenside castling
            rook_queenside = board[king_row][0]
            if isinstance(rook_queenside, Rook) and rook_queenside.first_move:
                # Check if path is clear
                if all(board[king_row][col] is None for col in [1, 2]):
                    return "queenside"

            # Check kingside castling
            rook_kingside = board[king_row][7]
            if isinstance(rook_kingside, Rook) and rook_kingside.first_move:
                # Check if path is clear
                if all(board[king_row][col] is None for col in [5, 6]):
                    return "kingside"

        except Exception as e:
            logger.error(f"Error in castling: {e}")
        return False

    """
    Take piece xy coords and end square xy coords
    Checks all legal moves as well as enpesaunt moves
    Returns True for a legal move
    Returns False for an illegal move
    """

    @track_performance(op="move", name="move_piece")
    def move_piece(self, x, y, endx, endy):
        try:
            with measure_operation(
                "validate_move",
                "move_validation",
                tags={"start_pos": f"{x},{y}", "end_pos": f"{endx},{endy}"},
            ):
                # Update Sentry context with move information
                sentry_sdk.set_context(
                    "move",
                    {
                        "game_id": self.game_id,
                        "move_count": self.move_count,
                        "player_turn": self.player_turn,
                        "from_pos": f"{x},{y}",
                        "to_pos": f"{endx},{endy}",
                    },
                )

                # where there is no piece return False
                if self.board[x][y] is None:
                    logger.warning("No piece at this position")
                    return False

                # check if it's the correct turn
                if self.board[x][y].colour != self.player_turn:
                    logger.warning(f"It's {self.player_turn}'s turn")
                    return False

                # enpesaunt rules
                is_enpesaunt = self.enpesaunt(x, y, self.board[x][y].colour)

                # castling rules
                is_castling = self.castling(self.board, self.board[x][y].colour)

                # if the end pos is not in the valid moves return False
                valid_moves = self.board[x][y].get_valid_moves(self.board, x, y)
                if (
                    ((endx, endy) not in valid_moves)
                    and not is_enpesaunt
                    and not is_castling  # returns False if no castling opportunity
                ):
                    logger.warning("Invalid move, not legal")
                    return False

                # Make a temporary move to check if it would put us in check
                temp_board = [[None for _ in range(8)] for _ in range(8)]
                # Copy all pieces to temp board
                for i in range(8):
                    for j in range(8):
                        piece = self.board[i][j]
                        if piece:
                            # Create a new piece of the same type and color
                            piece_type = type(piece)
                            new_piece = piece_type(piece.colour)
                            # Copy all attributes from the original piece
                            for attr in dir(piece):
                                if not attr.startswith("__") and not callable(
                                    getattr(piece, attr)
                                ):
                                    setattr(new_piece, attr, getattr(piece, attr))
                            temp_board[i][j] = new_piece

                # Store the captured piece if any
                captured_piece = temp_board[endx][endy]

                # Make the move on the temporary board
                temp_board[endx][endy] = temp_board[x][y]
                temp_board[x][y] = None

                # Check if this move would leave us in check
                check_status = self.check_position(temp_board, self.player_turn)
                if check_status > 0:  # Either in check (1) or checkmate (2)
                    logger.warning(
                        f"Invalid move - would leave us in check (status: {check_status})"
                    )
                    return False

                # remove enpesaunt pawn
                if is_enpesaunt:
                    if isinstance(self.board[x][y], Pawn) and abs(x - endx) == 2:
                        if isinstance(self.board[endx][endy + 1], Pawn):
                            self.board[endx][endy + 1] = None
                        elif isinstance(self.board[endx][endy - 1], Pawn):
                            self.board[endx][endy - 1] = None

                # handle castling
                if is_castling and (
                    isinstance(self.board[x][y], Rook)
                    or isinstance(self.board[x][y], King)
                ):
                    if endy == 2:  # queenside castling
                        self.board[endx][endy] = self.board[x][y]
                        self.board[x][y] = None
                        self.board[endx][3] = self.board[endx][0]
                        self.board[endx][0] = None
                    elif endy == 6:  # kingside castling
                        self.board[endx][endy] = self.board[x][y]
                        self.board[x][y] = None
                        self.board[endx][5] = self.board[endx][7]
                        self.board[endx][7] = None

                # handle pawn promotion
                if isinstance(self.board[x][y], Pawn):
                    match endx:
                        case 7:
                            self.promote_pawn(endx, endy, piece=Queen)
                        case 0:
                            self.promote_pawn(endx, endy, piece=Queen)

                # update the material
                if captured_piece is not None:
                    self.material += captured_piece.weight

                # increment the move count
                self.move_count += 1

                # Track the actual move operation
                with measure_operation(
                    "execute_move",
                    "move_execution",
                    tags={
                        "piece_type": self.board[x][y].__class__.__name__,
                        "player": self.player_turn,
                    },
                ):
                    piece = self.board[x][y]
                    logger.info(
                        f"Moving piece: {piece.__class__.__name__} from ({x}, {y}) to ({endx}, {endy})"
                    )
                    self.board[endx][endy] = piece
                    self.board[x][y] = None

                # switch the turn
                self.player_turn = "black" if self.player_turn == "white" else "white"
                logger.info("Move successful")

                logger.debug(
                    f"{piece.__class__.__name__} moved to ({endx}, {endy})"
                    + (
                        f", captured {captured_piece.__class__.__name__}"
                        if captured_piece
                        else ""
                    )
                )

                logger.debug(f"Valid Moves: {valid_moves}")
                # Display the updated board
                self.display_board_as_text()

                # If it's black's turn after a successful white move, make an automatic move
                if self.player_turn == "black":
                    # Find all black pieces and their valid moves
                    black_moves = []
                    for i in range(8):
                        for j in range(8):
                            piece = self.board[i][j]
                            if piece and piece.colour == "black":
                                moves = piece.get_valid_moves(self.board, i, j)
                                for move in moves:
                                    black_moves.append((i, j, move[0], move[1]))

                    # Evaluate each move
                    best_move = None
                    best_score = float("-inf")
                    for move in black_moves:
                        # Check if move is legal (doesn't leave us in check)
                        start_x, start_y, end_x, end_y = move
                        temp_board = [[None for _ in range(8)] for _ in range(8)]
                        for i in range(8):
                            for j in range(8):
                                piece = self.board[i][j]
                                if piece:
                                    piece_type = type(piece)
                                    new_piece = piece_type(piece.colour)
                                    for attr in dir(piece):
                                        if not attr.startswith("__") and not callable(
                                            getattr(piece, attr)
                                        ):
                                            setattr(
                                                new_piece, attr, getattr(piece, attr)
                                            )
                                    temp_board[i][j] = new_piece

                        temp_board[end_x][end_y] = temp_board[start_x][start_y]
                        temp_board[start_x][start_y] = None

                        if self.check_position(temp_board, "black") == 0:
                            # Evaluate the move
                            score = self.evaluate_move(self.board, move, "black")
                            if score > best_score:
                                best_score = score
                                best_move = move

                    if best_move:
                        start_x, start_y, end_x, end_y = best_move
                        logger.info(
                            f"Black automatically moving from ({start_x}, {start_y}) to ({end_x}, {end_y}) with score {best_score}"
                        )
                        self.move_piece(start_x, start_y, end_x, end_y)

                return True
        except Exception as e:
            logger.error(f"Error moving piece: {e}")
            sentry_sdk.capture_exception(e)
            return False

    def check_position(self, board_state, player_colour):
        """Check if a player is in check in a given board position"""
        try:
            # Find the king's position
            king_position = None
            for x in range(8):
                for y in range(8):
                    piece = board_state[x][y]
                    if isinstance(piece, King) and piece.colour == player_colour:
                        king_position = (x, y)
                        break
                if king_position:
                    break

            if not king_position:
                logger.warning(f"No {player_colour} king found on the board")
                return 0

            king_x, king_y = king_position
            logger.debug(
                f"Checking if {player_colour} king at ({king_x}, {king_y}) is in check"
            )

            # Check if any opponent piece can attack the king
            for x in range(8):
                for y in range(8):
                    piece = board_state[x][y]
                    if piece is not None and piece.colour != player_colour:
                        try:
                            # Get valid moves for the piece
                            valid_moves = piece.get_valid_moves(board_state, x, y)

                            # If king's position is in valid moves, check if path is clear
                            if (king_x, king_y) in valid_moves:
                                # For sliding pieces (Queen, Rook, Bishop), verify path is clear
                                if isinstance(piece, (Queen, Rook, Bishop)):
                                    # Calculate direction vector
                                    dx = (
                                        0
                                        if king_x == x
                                        else (king_x - x) // abs(king_x - x)
                                    )
                                    dy = (
                                        0
                                        if king_y == y
                                        else (king_y - y) // abs(king_y - y)
                                    )

                                    # Check each square in the path
                                    curr_x, curr_y = x + dx, y + dy
                                    path_clear = True

                                    while (curr_x, curr_y) != (king_x, king_y):
                                        if board_state[curr_x][curr_y] is not None:
                                            path_clear = False
                                            break
                                        curr_x += dx
                                        curr_y += dy

                                    if path_clear:
                                        logger.debug(
                                            f"{player_colour} king in check from {piece.__class__.__name__} at ({x}, {y})"
                                        )
                                        return 1  # Check
                                else:  # For non-sliding pieces (Knight, Pawn)
                                    logger.debug(
                                        f"{player_colour} king in check from {piece.__class__.__name__} at ({x}, {y})"
                                    )
                                    return 1  # Check
                        except Exception as e:
                            logger.error(
                                f"Error checking moves for piece at ({x},{y}): {e}"
                            )
                            continue

            logger.debug(f"{player_colour} king is not in check")
            return 0  # No check
        except Exception as e:
            logger.error(f"Error checking position: {e}")
            return 0  # Safe default

    """
    Promotes a pawn to a queen, rook, bishop, or knight
    base on piece
    """

    def promote_pawn(self, x, y, piece):
        logger.info(f"Promoting pawn at ({x}, {y}) to {piece.__name__}")
        logger.debug(self.board[x][y].__class__.__name__)

        colour = self.board[x][y].colour
        self.board[x][y] = piece(colour)

    """
    Takes No arguments and returns a number based on weather the player is in check
    """

    @track_slow_operations(threshold_seconds=0.5)
    def game_over(self):
        result = (
            self.are_you_in_check("white") == 2 or self.are_you_in_check("black") == 2
        )
        logger.info(f"Game over = {result}")
        return result

    """
    Takes the colour of the player
    Returns the x and y of the king
    """

    def get_king_position(self, colour):
        for x in range(8):
            for y in range(8):
                if (
                    isinstance(self.board[x][y], King)
                    and self.board[x][y].colour == colour
                ):
                    position = (x, y)
                    logger.debug(f"King position for {colour}: {position}")
                    return position

    """
    Takes the colour of the player
    Returns:
    2 for checkmate
    1 for check
    0 for no check
    """

    @track_performance(op="check", name="check_status")
    def are_you_in_check(self, player_colour):
        try:
            with sentry_sdk.start_span(
                op="chess.check_status", description=f"Check status for {player_colour}"
            ) as span:
                span.set_tag("player_color", player_colour)

                king_position = self.get_king_position(player_colour)
                if not king_position:
                    logger.warning(f"No {player_colour} king found on the board")
                    return 0

                king_x, king_y = king_position
                logger.debug(
                    f"Checking if {player_colour} king at ({king_x}, {king_y}) is in check"
                )

                # Check if any of the opponent's pieces can move to the king's position
                for x in range(8):
                    for y in range(8):
                        piece = self.board[x][y]
                        if piece is not None and piece.colour != player_colour:
                            try:
                                valid_moves = piece.get_valid_moves(self.board, x, y)
                                # Check if king's position is in the valid moves
                                if (king_x, king_y) in valid_moves:
                                    logger.debug(
                                        f"King in check from {piece.__class__.__name__} at ({x}, {y})"
                                    )
                                    # Check for checkmate
                                    if self.is_checkmate(player_colour, king_position):
                                        logger.info(
                                            f"{player_colour} king is in checkmate"
                                        )
                                        return 2  # Checkmate
                                    logger.info(f"{player_colour} king is in check")
                                    return 1  # Check
                            except Exception as e:
                                logger.error(
                                    f"Error checking moves for piece at ({x},{y}): {e}"
                                )
                                continue
                logger.debug(f"{player_colour} king is not in check")
                return 0  # No check
        except Exception as e:
            logger.error(f"Error checking check status: {e}")
            sentry_sdk.capture_exception(e)
            return 0  # Safe default - no check

    def is_checkmate(self, player_colour, king_position):
        """Check if the king is in checkmate"""
        try:
            with sentry_sdk.start_span(
                op="chess.checkmate_check",
                description=f"Check checkmate for {player_colour}",
            ) as span:
                span.set_tag("player_color", player_colour)
                span.set_tag("king_position", f"{king_position[0]},{king_position[1]}")

                king_x, king_y = king_position
                logger.debug(
                    f"Checking if {player_colour} king at ({king_x}, {king_y}) is in checkmate"
                )

                # First check if any other piece can capture the attacking piece or block the check
                attacking_pieces = []
                attacking_positions = []

                # Find all pieces attacking the king
                for x in range(8):
                    for y in range(8):
                        piece = self.board[x][y]
                        if piece and piece.colour != player_colour:
                            try:
                                valid_moves = piece.get_valid_moves(self.board, x, y)
                                if (king_x, king_y) in valid_moves:
                                    attacking_pieces.append((x, y))
                                    attacking_positions.append((x, y))
                            except Exception:
                                continue

                # For each friendly piece, see if it can capture an attacking piece or block the check
                for x in range(8):
                    for y in range(8):
                        piece = self.board[x][y]
                        if (
                            piece
                            and piece.colour == player_colour
                            and not isinstance(piece, King)
                        ):
                            try:
                                valid_moves = piece.get_valid_moves(self.board, x, y)
                                for attack_pos in attacking_positions:
                                    if attack_pos in valid_moves:
                                        # Can capture attacking piece
                                        logger.debug(
                                            f"Checkmate prevented: {piece.__class__.__name__} at ({x}, {y}) can capture attacking piece"
                                        )
                                        return False
                            except Exception:
                                continue

                # Try all possible king moves
                king = self.board[king_x][king_y]
                if not king:
                    return False

                # Get all potential moves for the king
                try:
                    king_moves = king.get_valid_moves(self.board, king_x, king_y)
                except Exception:
                    return False

                # For each potential king move, see if it's still in check
                for move_x, move_y in king_moves:
                    # Make temporary move
                    temp_board = copy.deepcopy(self.board)
                    temp_board[move_x][move_y] = temp_board[king_x][king_y]
                    temp_board[king_x][king_y] = None

                    # Check if this position is still in check
                    still_in_check = False
                    for x in range(8):
                        for y in range(8):
                            piece = temp_board[x][y]
                            if piece and piece.colour != player_colour:
                                try:
                                    valid_moves = piece.get_valid_moves(
                                        temp_board, x, y
                                    )
                                    if (move_x, move_y) in valid_moves:
                                        still_in_check = True
                                        break
                                except Exception:
                                    continue
                        if still_in_check:
                            break

                    if not still_in_check:
                        # Found a safe move for the king
                        logger.debug(
                            f"Checkmate prevented: King can move to ({move_x}, {move_y})"
                        )
                        return False

                logger.info(
                    f"{player_colour} king is in checkmate - no legal moves available"
                )
                return True  # No escape moves found - checkmate
        except Exception as e:
            logger.error(f"Error checking checkmate: {e}")
            sentry_sdk.capture_exception(e)
            return False

    def evaluate_position(self, board_state, color):
        """Evaluate the position for the given color"""
        score = 0

        # Material value and piece-square tables
        piece_values = {
            Pawn: 100,
            Knight: 320,
            Bishop: 330,
            Rook: 500,
            Queen: 900,
            King: 20000,
        }

        # Center control bonus
        center_squares = [(3, 3), (3, 4), (4, 3), (4, 4)]
        center_control = 30
        extended_center_squares = [
            (2, 2),
            (2, 3),
            (2, 4),
            (2, 5),
            (3, 2),
            (3, 5),
            (4, 2),
            (4, 5),
            (5, 2),
            (5, 3),
            (5, 4),
            (5, 5),
        ]
        extended_center_control = 15

        # Piece development and mobility
        developed_pawn_rank = 3 if color == "white" else 4

        for x in range(8):
            for y in range(8):
                piece = board_state[x][y]
                if piece is not None:
                    multiplier = 1 if piece.colour == color else -1

                    # Base material value
                    score += piece_values[type(piece)] * multiplier

                    # Position-based bonuses
                    if isinstance(piece, Pawn):
                        # Pawn structure
                        if piece.colour == color:
                            # Advancement bonus
                            if color == "white":
                                score += 10 * (x - 1)  # Bonus for advancing
                            else:
                                score += 10 * (6 - x)  # Bonus for advancing

                            # Passed pawn bonus
                            is_passed = True
                            pawn_direction = 1 if color == "white" else -1
                            for check_x in range(
                                x + pawn_direction,
                                8 if color == "white" else -1,
                                pawn_direction,
                            ):
                                if 0 <= check_x < 8 and (
                                    (
                                        y > 0
                                        and isinstance(
                                            board_state[check_x][y - 1], Pawn
                                        )
                                    )
                                    or isinstance(board_state[check_x][y], Pawn)
                                    or (
                                        y < 7
                                        and isinstance(
                                            board_state[check_x][y + 1], Pawn
                                        )
                                    )
                                ):
                                    is_passed = False
                                    break
                            if is_passed:
                                score += 50

                    elif isinstance(piece, Knight):
                        # Knights are more valuable in closed positions
                        if piece.colour == color:
                            valid_moves = piece.get_valid_moves(board_state, x, y)
                            score += len(valid_moves) * 10  # Mobility bonus

                            # Outpost bonus - knight protected by pawn and can't be attacked by enemy pawns
                            if color == "white" and x > 3:
                                if (
                                    y > 0
                                    and isinstance(board_state[x - 1][y - 1], Pawn)
                                    and board_state[x - 1][y - 1].colour == color
                                ):
                                    score += 30
                            elif color == "black" and x < 4:
                                if (
                                    y > 0
                                    and isinstance(board_state[x + 1][y - 1], Pawn)
                                    and board_state[x + 1][y - 1].colour == color
                                ):
                                    score += 30

                    elif isinstance(piece, Bishop):
                        if piece.colour == color:
                            valid_moves = piece.get_valid_moves(board_state, x, y)
                            score += len(valid_moves) * 8  # Mobility bonus

                    elif isinstance(piece, Rook):
                        if piece.colour == color:
                            # Bonus for rooks on open files
                            open_file = True
                            for check_x in range(8):
                                if isinstance(board_state[check_x][y], Pawn):
                                    open_file = False
                                    break
                            if open_file:
                                score += 30

                    elif isinstance(piece, Queen):
                        if piece.colour == color:
                            valid_moves = piece.get_valid_moves(board_state, x, y)
                            score += len(valid_moves) * 5  # Mobility bonus

                    elif isinstance(piece, King):
                        if piece.colour == color:
                            # King safety
                            if self.is_endgame(board_state):
                                # King should be active in endgame
                                valid_moves = piece.get_valid_moves(board_state, x, y)
                                score += len(valid_moves) * 8
                            else:
                                # King safety in middlegame
                                if color == "white" and x < 2:
                                    score += 60  # Bonus for castled position
                                elif color == "black" and x > 5:
                                    score += 60  # Bonus for castled position

                    # Center control
                    if (x, y) in center_squares:
                        score += center_control * multiplier
                    elif (x, y) in extended_center_squares:
                        score += extended_center_control * multiplier

        return score

    def is_endgame(self, board_state):
        """Determine if the position is in endgame"""
        queens = 0
        minor_pieces = 0
        for x in range(8):
            for y in range(8):
                piece = board_state[x][y]
                if isinstance(piece, Queen):
                    queens += 1
                elif isinstance(piece, (Bishop, Knight)):
                    minor_pieces += 1
        return queens == 0 or (queens == 2 and minor_pieces <= 2)

    def evaluate_move(self, board_state, move, color):
        """Evaluate a specific move"""
        start_x, start_y, end_x, end_y = move
        score = 0

        # Create a temporary board with the move applied
        temp_board = [[None for _ in range(8)] for _ in range(8)]
        for i in range(8):
            for j in range(8):
                piece = board_state[i][j]
                if piece:
                    piece_type = type(piece)
                    new_piece = piece_type(piece.colour)
                    for attr in dir(piece):
                        if not attr.startswith("__") and not callable(
                            getattr(piece, attr)
                        ):
                            setattr(new_piece, attr, getattr(piece, attr))
                    temp_board[i][j] = new_piece

        # Apply the move
        captured_piece = temp_board[end_x][end_y]
        temp_board[end_x][end_y] = temp_board[start_x][start_y]
        temp_board[start_x][start_y] = None

        # Get the position evaluation after the move
        score = self.evaluate_position(temp_board, color)

        # Additional move-specific considerations
        piece = board_state[start_x][start_y]

        # Avoid moving the same piece twice in the opening
        if (
            self.move_count < 10
            and hasattr(piece, "first_move")
            and not piece.first_move
        ):
            score -= 20

        # Encourage development in the opening
        if (
            self.move_count < 10
            and isinstance(piece, (Rook, King))
            and hasattr(piece, "first_move")
            and piece.first_move
        ):
            score += 30

        # Penalty for moving the king early (except castling)
        if (
            isinstance(piece, King)
            and hasattr(piece, "first_move")
            and piece.first_move
            and self.move_count < 10
        ):
            if abs(end_y - start_y) != 2:  # Not castling
                score -= 100

        return score

    """
    Takes no arguments
    calls other function
    """

    def main(self):
        logger.info("Starting main game loop")
        while not self.game_over():
            #! DEBUG TEMP REMOVE THIS
            # self.display_board_as_coordinates()
            self.display_board_as_text()
            elapsed_time = time.time() - self.start_time  # Calculate elapsed time
            logger.info(f"Move count: {self.move_count}")
            logger.info(f"Elapsed time: {elapsed_time:.2f} seconds")
            logger.info(f"{self.player_turn.capitalize()} to move")
            x, y, endx, endy = map(int, input("Enter move: ").split())
            if self.move_piece(x, y, endx, endy):
                self.player_turn = "black" if self.player_turn == "white" else "white"
            else:
                logger.warning("Invalid move")
        logger.info("Game over")


if __name__ == "__main__":
    logger.info("Starting ChessBoard application")
    board_instance = ChessBoard()
    board_instance.main()
