# define the default parent piece class
class Piece:
    def __init__(self, colour):
        self.colour = colour
        self.x = int
        self.y = int
        self.selected = False

    def select(self):
        self.selected = True

    def deselect(self):
        self.selected = False


class Rook(Piece):
    def __init__(self, colour):
        super().__init__(colour)
        self.first_move = True
        self.weight = 5
        if self.colour == "white":
            self.symbol = "R"
        else:
            self.symbol = "r"

    def get_valid_moves(self, board, x, y):
        valid_moves = []

        # Check boundaries first
        if not (0 <= x < 8 and 0 <= y < 8):
            return valid_moves

        # check if the square in front of the rook is empty
        def front(x, y, valid_moves):
            for i in range(1, 8):
                if y + i <= 7:
                    if board[x][y + i] is None:
                        valid_moves.append((x, y + i))
                    elif board[x][y + i].colour != board[x][y].colour:
                        valid_moves.append((x, y + i))
                        break
                    else:
                        break
                else:
                    break
            return valid_moves

        valid_moves = front(x, y, valid_moves)

        # check if the square behind the rook is empty
        def back(x, y, valid_moves):
            for i in range(1, 8):
                if y - i >= 0:
                    if board[x][y - i] is None:
                        valid_moves.append((x, y - i))
                    elif board[x][y - i].colour != board[x][y].colour:
                        valid_moves.append((x, y - i))
                        break
                    else:
                        break
            return valid_moves

        valid_moves = back(x, y, valid_moves)

        # check if the square to the left of the rook is empty
        def left(x, y, valid_moves):
            for i in range(1, 8):
                if x + i <= 7:
                    if board[x + i][y] is None:
                        valid_moves.append((x + i, y))
                    elif board[x + i][y].colour != board[x][y].colour:
                        valid_moves.append((x + i, y))
                        break
                    else:
                        break
            return valid_moves

        valid_moves = left(x, y, valid_moves)

        # check if the square to the right of the rook is empty
        def right(x, y, valid_moves):
            for i in range(1, 8):
                if x - i >= 0:
                    if board[x - i][y] is None:
                        valid_moves.append((x - i, y))
                    elif board[x - i][y].colour != board[x][y].colour:
                        valid_moves.append((x - i, y))
                        break
                    else:
                        break
            return valid_moves

        valid_moves = right(x, y, valid_moves)

        """
        def run_cpu_tasks_in_parallel(tasks, x, y, valid_moves):
            with ProcessPoolExecutor() as executor:
                futures = [executor.submit(task, x, y, valid_moves) for task in tasks]
                for future in futures:
                    valid_moves = future.result()
            return valid_moves

        valid_moves = right(x, y, valid_moves)

        # Get all valid moves simultaneously and return the list

        all_moves = [front, back, left, right]
        valid_moves = run_cpu_tasks_in_parallel(all_moves, x, y, valid_moves)

        """
        return valid_moves


class Knight(Piece):
    def __init__(self, colour):
        super().__init__(colour)
        self.weight = 3
        if self.colour == "white":
            self.symbol = "N"
        else:
            self.symbol = "n"

    def get_valid_moves(self, board, x, y):
        valid_moves = []
        # calculate all L shaped moves
        moves = [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]
        for dx, dy in moves:
            nx, ny = x + dx, y + dy
            if 0 <= nx < 8 and 0 <= ny < 8:
                if board[nx][ny] is None or board[nx][ny].colour != self.colour:
                    valid_moves.append((nx, ny))
        return valid_moves


class Bishop(Piece):
    def __init__(self, colour):
        super().__init__(colour)
        self.weight = 3
        if self.colour == "white":
            self.symbol = "B"
        else:
            self.symbol = "b"

    def get_valid_moves(self, board, x, y):
        valid_moves = []

        # Check boundaries first
        if not (0 <= x < 8 and 0 <= y < 8):
            return valid_moves

        i = 1

        # Check diagonal up-right
        def diagonal_up_right(self, i, valid_moves):
            while x + i <= 7 and y + i <= 7:
                if board[x + i][y + i] is None:
                    valid_moves.append((x + i, y + i))
                elif board[x + i][y + i].colour != self.colour:
                    valid_moves.append((x + i, y + i))
                    break
                else:
                    break
                i += 1
            return valid_moves

        valid_moves = diagonal_up_right(self, i, valid_moves)

        # Check diagonal up-left
        def diagonal_up_left(self, i, valid_moves):
            while x + i <= 7 and y - i >= 0:
                if board[x + i][y - i] is None:
                    valid_moves.append((x + i, y - i))
                elif board[x + i][y - i].colour != self.colour:
                    valid_moves.append((x + i, y - i))
                    break
                else:
                    break
                i += 1
            return valid_moves

        valid_moves = diagonal_up_left(self, i, valid_moves)

        # Check diagonal down-right
        def diagonal_down_left(self, i, valid_moves):
            while x - i >= 0 and y + i <= 7:
                if board[x - i][y + i] is None:
                    valid_moves.append((x - i, y + i))
                elif board[x - i][y + i].colour != self.colour:
                    valid_moves.append((x - i, y + i))
                    break
                else:
                    break
                i += 1
            return valid_moves

        valid_moves = diagonal_down_left(self, i, valid_moves)

        # Check diagonal down-left
        def diagonal_down_left(self, i, valid_moves):
            while x - i >= 0 and y - i >= 0:
                if board[x - i][y - i] is None:
                    valid_moves.append((x - i, y - i))
                elif board[x - i][y - i].colour != self.colour:
                    valid_moves.append((x - i, y - i))
                    break
                else:
                    break
                i += 1
            return valid_moves

        valid_moves = diagonal_down_left(self, i, valid_moves)

        return valid_moves


class Queen(Piece):
    def __init__(self, colour):
        super().__init__(colour)
        self.weight = 9
        if self.colour == "white":
            self.symbol = "Q"
        else:
            self.symbol = "q"

    def get_valid_moves(self, board, x, y):
        valid_moves = []

        # Check boundaries first
        if not (0 <= x < 8 and 0 <= y < 8):
            return valid_moves

        # Get all valid diagonal and straight moves
        directions = [
            (0, 1),
            (0, -1),
            (1, 0),
            (-1, 0),  # Rook moves
            (1, 1),
            (1, -1),
            (-1, 1),
            (-1, -1),  # Bishop moves
        ]

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            while 0 <= nx < 8 and 0 <= ny < 8:  # Stay within board boundaries
                if board[nx][ny] is None:
                    valid_moves.append((nx, ny))
                elif board[nx][ny].colour != self.colour:
                    valid_moves.append((nx, ny))
                    break
                else:
                    break
                nx, ny = nx + dx, ny + dy

        return valid_moves


class King(Piece):
    def __init__(self, colour):
        super().__init__(colour)
        self.first_move = True
        self.weight = 0
        if self.colour == "white":
            self.symbol = "K"
        else:
            self.symbol = "k"

    def get_valid_moves(self, board, x, y):
        valid_moves = []

        # Check boundaries first
        if not (0 <= x < 8 and 0 <= y < 8):
            return valid_moves

        directions = [
            (0, 1),
            (0, -1),
            (1, 0),
            (-1, 0),
            (1, 1),
            (1, -1),
            (-1, 1),
            (-1, -1),
        ]

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < 8 and 0 <= ny < 8:  # Stay within board boundaries
                if board[nx][ny] is None or board[nx][ny].colour != self.colour:
                    valid_moves.append((nx, ny))

        return valid_moves


class Pawn(Piece):
    def __init__(self, colour):
        super().__init__(colour)
        self.first_move = True
        self.weight = 1
        if self.colour == "white":
            self.symbol = "P"
        else:
            self.symbol = "p"

    def get_valid_moves(self, board, x, y):
        valid_moves = []

        # Determine the direction of movement based on the color of the pawn
        direction = 1 if self.colour == "white" else -1

        # Check board boundaries before accessing cells
        # Check forward move - one square
        if 0 <= x + direction < 8:  # Check if next position is within board
            if board[x + direction][y] is None:
                valid_moves.append((x + direction, y))

                # If it's the pawn's first move, check if it can move two squares
                if self.first_move and 0 <= x + 2 * direction < 8:
                    if board[x + 2 * direction][y] is None:
                        valid_moves.append((x + 2 * direction, y))

        # Check diagonal captures - left side
        if 0 <= x + direction < 8 and 0 <= y - 1 < 8:
            if (
                board[x + direction][y - 1] is not None
                and board[x + direction][y - 1].colour != self.colour
            ):
                valid_moves.append((x + direction, y - 1))

        # Check diagonal captures - right side
        if 0 <= x + direction < 8 and 0 <= y + 1 < 8:
            if (
                board[x + direction][y + 1] is not None
                and board[x + direction][y + 1].colour != self.colour
            ):
                valid_moves.append((x + direction, y + 1))

        return valid_moves
