import chess
import time
import csv
import logging  # Add logging import

from pieces import Bishop, King, Knight, Pawn, Queen, Rook

# Configure logging
logging.basicConfig(
    level=logging.WARNING, format="%(asctime)s - %(levelname)s - %(message)s"
)


class ChessBoard:
    def __init__(self):
        logging.info("Initializing ChessBoard")
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
        logging.info("ChessBoard initialized")

    def load_openings(self, file_path):
        logging.info(f"Loading openings from {file_path}")
        openings = {}
        print("path:", file_path)
        with open(file_path, newline="", encoding="utf-8") as tsvfile:
            reader = csv.reader(tsvfile, delimiter="\t")
            for row in reader:
                if len(row) >= 3:
                    name = row[1]
                    moves = row[2]
                    openings[moves] = name
        return openings

    def get_opening(self):
        current_moves = " ".join(self.get_epd())
        for moves, name in self.openings.items():
            if current_moves.startswith(moves):
                opening = name
                logging.debug(f"Current opening: {opening}")
                return opening
        return "Unknown Opening"

    """
    Takes no arguments
    Returns a EPD string
    """

    def get_epd(self):
        # convert to EPD (FEN with no move numbers)
        board = chess.Board(self.board_array_to_fen())
        epd = board.epd()
        print(epd)
        logging.debug(f"EPD: {epd}")
        return epd

    """
    Takes no arguments
    Returns an array of moves that are legal
    """

    def get_all_valid_moves(self):
        board = chess.Board(self.board_array_to_fen())
        valid_moves = [move.uci() for move in board.legal_moves]
        print(valid_moves)
        logging.debug(f"All valid moves: {valid_moves}")
        return valid_moves

    """
    Takes no arguments
    Returns the board as a FEN string
    """

    def board_array_to_fen(self):
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

    """
    Takes no arguments
    Returns the material as a positive or negative number
    Value is positive for white and negative for black
    """

    def get_material_count(self, colour):
        material = 0
        for x in range(8):
            for y in range(8):
                if self.board[x][y] is not None:
                    if self.board[x][y].colour == colour:
                        material += self.board[x][y].weight
                    else:
                        material -= self.board[x][y].weight
        logging.debug(f"Material count for {colour}: {material}")
        return material

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
            print(self.board_cache[i * 8 : i * 8 + 8])
        logging.debug("Board displayed as text")

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
            print(colours[i * 8 : i * 8 + 8])
        logging.debug("Board displayed as colours")

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
            print(coordinates[i * 8 : i * 8 + 8])
        logging.debug("Board displayed as coordinates")

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
                    print("pawn on ", x, y + 1)
                    result = True
                    logging.debug(
                        f"En passant check at ({x}, {y}) for {colour}: {result}"
                    )
                    return result
                elif (
                    isinstance(self.board[x][y - 1], Pawn)
                    and self.board[x][y - 1].colour != colour
                    and self.board[x][y - 1].first_move
                    and self.board[x + direction][y - 1] is None
                ):
                    print("pawn on", x, y - 1)
                    result = True
                    logging.debug(
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
                    logging.debug(f"Castling check for {player_colour}: {result}")
                    return result

                if board[0][7].first_move:
                    result = "kingside"
                    logging.debug(f"Castling check for {player_colour}: {result}")
                    return result

            if player_colour == "black" and (board[7][3].first_move):
                # king can castle
                if board[7][0].first_move:
                    result = "queenside"
                    logging.debug(f"Castling check for {player_colour}: {result}")
                    return result

                if board[7][7].first_move:
                    result = "kingside"
                    logging.debug(f"Castling check for {player_colour}: {result}")
                    return result
        except Exception as e:
            print(e)
        return False

    """
    Take piece xy coords and end square xy coords
    Checks all legal moves as well as enpesaunt moves
    Returns True for a legal move
    Returns False for an illegal move
    """

    def move_piece(self, x, y, endx, endy):
        logging.info(f"Attempting to move piece from ({x}, {y}) to ({endx}, {endy})")
        # where there is no piece return False
        if self.board[x][y] is None:
            logging.warning("No piece at this position")
            return False

        # check if it's the correct turn
        if self.board[x][y].colour != self.player_turn:
            logging.warning(f"It's {self.player_turn}'s turn")
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
            logging.warning("Invalid move, not legal")
            return False

        # check if the move caused the player to be in check
        if self.are_you_in_check(self.player_turn) == (1 or 2):
            logging.warning("Invalid move (check)")
            return False

        # remove enpesaunt pawn
        if is_enpesaunt:
            if isinstance(self.board[x][y], Pawn) and abs(x - endx) == 2:
                if isinstance(self.board[endx][endy + 1], Pawn):
                    self.board[endx][endy + 1] = None
                elif isinstance(self.board[endx][endy - 1], Pawn):
                    self.board[endx][endy - 1] = None

        # handle castling
        if is_castling:
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

        # move the actual piece
        logging.info(f"Endx, Endy: {self.board[endx][endy]}")
        self.board[endx][endy] = self.board[x][y]
        logging.info(f"X, Y: {self.board[x][y]}")
        self.board[x][y] = None

        # switch the turn
        self.player_turn = "black" if self.player_turn == "white" else "white"
        logging.info("Move successful")

        logging.debug(
            f"{self.board[x][y].__class__.__name__} moved to ({endx}, {endy}) , {self.board[endx][endy].__class__.__name__} at ({x}, {y}) removed"
        )

        # Display the updated board
        self.display_board_as_text()

        return True

    """
    Promotes a pawn to a queen, rook, bishop, or knight
    base on piece
    """

    def promote_pawn(self, x, y, piece):
        logging.info(f"Promoting pawn at ({x}, {y}) to {piece.__name__}")
        print(self.board[x][y].__class__.__name__)

        colour = self.board[x][y].colour
        self.board[x][y] = piece(colour)

    """
    Takes No arguments and returns a number based on weather the player is in check
    """

    def game_over(self):
        result = (
            self.are_you_in_check("white") == 2 or self.are_you_in_check("black") == 2
        )
        logging.info(f"Game over = {result}")
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
                    logging.debug(f"King position for {colour}: {position}")
                    return position

    """
    Takes no colour and returns
    2 for checkmate
    1 for check
    0 for no check
    """

    def are_you_in_check(self, player_colour):
        king_position = self.get_king_position(player_colour)

        # check if any of the opponent's pieces can move to the king's position
        for x in range(8):
            for y in range(8):
                piece = self.board[x][y]
                if piece is not None and piece.colour != player_colour:
                    try:
                        if king_position in piece.get_valid_moves(self.board, x, y):
                            # check if there are no valid moves that would result in the king not being in check
                            for dx in range(-1, 2):
                                for dy in range(-1, 2):
                                    new_x, new_y = (
                                        king_position[0] + dx,
                                        king_position[1] + dy,
                                    )
                                    if 0 <= new_x < 8 and 0 <= new_y < 8:
                                        # temporarily move the king
                                        temp = self.board[new_x][new_y]
                                        self.board[new_x][new_y] = self.board[
                                            king_position[0]
                                        ][king_position[1]]
                                        self.board[king_position[0]][
                                            king_position[1]
                                        ] = None
                                        # check if the king is still in check
                                        if not self.are_you_in_check(player_colour):
                                            # the king is not in check, so it's not checkmate
                                            # move the king back
                                            self.board[king_position[0]][
                                                king_position[1]
                                            ] = self.board[new_x][new_y]
                                            self.board[new_x][new_y] = temp
                                            status = 1  # for check
                                            logging.debug(
                                                f"Check status for {player_colour}: {status}"
                                            )
                                            return status
                                        # move the king back
                                        self.board[king_position[0]][
                                            king_position[1]
                                        ] = self.board[new_x][new_y]
                                        self.board[new_x][new_y] = temp
                            status = 2  # for checkmate
                            logging.debug(f"Check status for {player_colour}: {status}")
                            return status
                    except ValueError:  # catch ValueError: Outside of board
                        print("ValueError: Outside of board")
        status = 0  # for no check
        logging.debug(f"Check status for {player_colour}: {status}")
        return status

    """
    Takes no arguments
    calls other function
    """

    def main(self):
        logging.info("Starting main game loop")
        while not self.game_over():
            #! DEBUG TEMP REMOVE THIS
            # self.display_board_as_coordinates()
            self.display_board_as_text()
            print(f"Move count: {self.move_count}")  # Display move count
            elapsed_time = time.time() - self.start_time  # Calculate elapsed time
            print(f"Elapsed time: {elapsed_time:.2f} seconds")  # Display elapsed time
            logging.info(f"Move count: {self.move_count}")
            logging.info(f"Elapsed time: {elapsed_time:.2f} seconds")
            print(f"{self.player_turn.capitalize()} to move")
            logging.info(f"{self.player_turn.capitalize()} to move")
            x, y, endx, endy = map(int, input("Enter move: ").split())
            if self.move_piece(x, y, endx, endy):
                self.player_turn = "black" if self.player_turn == "white" else "white"
            else:
                print("Invalid move")

        logging.info("Game over")
        print("Game over")


if __name__ == "__main__":
    logging.info("Starting ChessBoard application")
    board_instance = ChessBoard()
    board_instance.main()
