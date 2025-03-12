import chess
import time
import csv
import copy
import sentry_sdk
from logging_config import get_logger

from chess import pgn

from pieces import Bishop, King, Knight, Pawn, Queen, Rook
import io

# Configure logging
logger = get_logger(__name__)

class ChessBoard:
    def __init__(self):
        try:
            logger.info("Initializing ChessBoard")
            self.move_count = 0
            self.player_turn = "white"
            self.material = -1
            self.start_time = time.time()  # Initialize start time

            self.board = [[None for _ in range(8)] for _ in range(8)]

            # Initialize board_cache with the correct size
            self.board_cache = ["|  |" for _ in range(64)]

            # Create white pieces
            self.board[0][0] = Rook("white")
            self.board[0][1] = Knight("white")
            self.board[0][2] = Bishop("white")
            self.board[0][4] = Queen("white")
            self.board[0][3] = King("white")
            self.board[0][5] = Bishop("white")
            self.board[0][6] = Knight("white")
            self.board[0][7] = Rook("white")
            for i in range(8):
                self.board[1][i] = Pawn("white")

            # Create black pieces
            self.board[7][0] = Rook("black")
            self.board[7][1] = Knight("black")
            self.board[7][2] = Bishop("black")
            self.board[7][4] = Queen("black")
            self.board[7][3] = King("black")
            self.board[7][5] = Bishop("black")
            self.board[7][6] = Knight("black")
            self.board[7][7] = Rook("black")
            for i in range(8):
                self.board[6][i] = Pawn("black")

            self.openings = self.load_openings("./openings/all.tsv")
            logger.info("ChessBoard initialized")
        except Exception as e:
            logger.error(f"Error initializing chess board: {e}")
            sentry_sdk.capture_exception(e)
            raise

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

    def castling(self, board, player_colour):
        # check if the king has moved
        try:
            if player_colour == "white" and (board[0][3].first_move):
                # king can castle
                if board[0][0].first_move:
                    result = "queenside"
                    logger.debug(f"Castling check for {player_colour}: {result}")
                    return result

                if board[0][7].first_move:
                    result = "kingside"
                    logger.debug(f"Castling check for {player_colour}: {result}")
                    return result

            if player_colour == "black" and (board[7][3].first_move):
                # king can castle
                if board[7][0].first_move:
                    result = "queenside"
                    logger.debug(f"Castling check for {player_colour}: {result}")
                    return result

                if board[7][7].first_move:
                    result = "kingside"
                    logger.debug(f"Castling check for {player_colour}: {result}")
                    return result
        except Exception as e:
            logger.error(f"Error in castling: {e}")
        return False

    """
    Take piece xy coords and end square xy coords
    Checks all legal moves as well as enpesaunt moves
    Returns True for a legal move
    Returns False for an illegal move
    """

    def move_piece(self, x, y, endx, endy):
        try:
            with sentry_sdk.start_span(
                op="chess.move_piece",
                description=f"Move piece from ({x},{y}) to ({endx},{endy})",
            ) as span:
                span.set_tag("start_pos", f"{x},{y}")
                span.set_tag("end_pos", f"{endx},{endy}")
                span.set_tag(
                    "piece_type",
                    self.board[x][y].__class__.__name__ if self.board[x][y] else "None",
                )
                span.set_tag("player_turn", self.player_turn)

                logger.info(
                    f"Attempting to move piece from ({x}, {y}) to ({endx}, {endy})"
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

                # check if the move caused the player to be in check
                if self.are_you_in_check(self.player_turn) == (1 or 2):
                    logger.warning("Invalid move (check)")
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
                if isinstance(self.board[endx][endy], Pawn):
                    match endx:
                        case 7:
                            self.promote_pawn(endx, endy, piece=Queen)
                        case 0:
                            self.promote_pawn(endx, endy, piece=Queen)

                # update the material
                if self.board[endx][endy] is not None:
                    self.material += self.board[endx][endy].weight

                # increment the move count
                self.move_count += 1

                # log the board state before the move
                logger.debug(f"Board state before move: {self.board}")

                # move the actual piece
                piece = self.board[x][y]
                logger.info(
                    f"Moving piece: {piece.__class__.__name__} from ({x}, {y}) to ({endx}, {endy})"
                )
                self.board[endx][endy] = piece
                self.board[x][y] = None

                # log the board state after the move
                logger.debug(f"Board state after move: {self.board}")

                # switch the turn
                self.player_turn = "black" if self.player_turn == "white" else "white"
                logger.info("Move successful")

                logger.debug(
                    f"{piece.__class__.__name__} moved to ({endx}, {endy}) , {self.board[endx][endy].__class__.__name__} at ({x}, {y}) removed"
                )

                logger.debug(f"Valid Moves: {valid_moves}")
                # Display the updated board
                self.display_board_as_text()

                return True
        except Exception as e:
            logger.error(f"Error moving piece: {e}")
            sentry_sdk.capture_exception(e)
            return False

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

                # Check if any of the opponent's pieces can move to the king's position
                for x in range(8):
                    for y in range(8):
                        piece = self.board[x][y]
                        if piece is not None and piece.colour != player_colour:
                            try:
                                valid_moves = piece.get_valid_moves(self.board, x, y)
                                # Check if king's position is in the valid moves
                                if king_position in valid_moves:
                                    # Check for checkmate
                                    if self.is_checkmate(player_colour, king_position):
                                        return 2  # Checkmate
                                    return 1  # Check
                            except Exception as e:
                                logger.error(
                                    f"Error checking moves for piece at ({x},{y}): {e}"
                                )
                                continue
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

                # Try all possible king moves
                king = self.board[king_x][king_y]
                if not king:
                    return False

                # Get all potential moves for the king
                try:
                    king_moves = king.get_valid_moves(self.board, king_x, king_y)
                except Exception:
                    # If we can't get moves, assume it's not checkmate
                    return False

                # If king has no valid moves, check if any piece can block the check
                if not king_moves:
                    # TODO: Check if any piece can block the check
                    return True

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

                # If any move escapes check, it's not checkmate
                if not still_in_check:
                    return False

            return True  # No escape moves found - checkmate
        except Exception as e:
            logger.error(f"Error checking checkmate: {e}")
            sentry_sdk.capture_exception(e)
            return False

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
