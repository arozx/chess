"""
mcts.py
This exists as a standalone component of a chess application
Uses a monte Carlo algorithm to generate moves with alpha beta pruning
The best move is returned as a array of tuples
"""

import math
import time
import random
import logging

from pieces import Bishop, King, Knight, Pawn, Queen, Rook
from eval_board import eval_board
from game_state import GameState

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Node:
    def __init__(self, state, parent=None, move_from_parent=None):
        if isinstance(state, GameState):
            self.state = state
        else:
            # Initialize with white's turn if creating new state
            self.state = GameState(state, "white")
        self.parent = parent
        self.move_from_parent = move_from_parent
        self.children = []
        self.visits = 0
        self.value = 0
        self._untried_moves = self._get_valid_moves()

    def _get_valid_moves(self):
        valid_moves = []
        board = self.state.board
        player_turn = self.state.player_turn

        if hasattr(board, "get_all_valid_moves"):
            valid_moves = board.get_all_valid_moves()
        else:
            # Handle list-based board
            for x in range(8):
                for y in range(8):
                    piece = board[x][y]
                    if piece and piece.colour == player_turn:
                        moves = piece.get_valid_moves(board, x, y)
                        valid_moves.extend([((x, y), move) for move in moves])
        return valid_moves

    def is_terminal(self):
        """A node is terminal if it has no valid moves left to try and no children"""
        if not self._untried_moves and not self.children:
            # Double check if we really have no valid moves
            current_moves = self._get_valid_moves()
            if not current_moves:
                return True
            # If we found moves, update untried moves
            self._untried_moves = current_moves
        return False

    def is_fully_expanded(self):
        """A node is fully expanded if it has no untried moves left"""
        if not self._untried_moves:
            # Double check if we missed any valid moves
            current_moves = self._get_valid_moves()
            if current_moves:
                self._untried_moves = current_moves
                return False
        return len(self._untried_moves) == 0

    def select_child(self):
        exploration = 1.4
        best_score = float("-inf")
        best_child = None

        for child in self.children:
            if child.visits == 0:
                return child

            exploitation = child.value / child.visits
            exploration_term = exploration * math.sqrt(
                math.log(self.visits) / child.visits
            )
            uct_score = exploitation + exploration_term

            if uct_score > best_score:
                best_score = uct_score
                best_child = child

        return best_child

    def expand(self):
        if not self._untried_moves:
            return self

        move = random.choice(self._untried_moves)
        self._untried_moves.remove(move)

        new_state = self.apply_move(self.state, move)
        if new_state is None:
            return self

        child = Node(new_state, parent=self, move_from_parent=move)
        self.children.append(child)
        return child

    def simulate(self):
        state = GameState.from_node_or_state(self.state)
        depth = 0
        max_depth = 50  # Prevent infinite loops

        while not self.is_terminal() and depth < max_depth:
            valid_moves = self._get_valid_moves()
            if not valid_moves:
                break

            move = random.choice(valid_moves)
            new_state = self.apply_move(state, move)
            if new_state is None:
                break
            state = new_state
            depth += 1

        # Use eval_board for the final evaluation
        if hasattr(state.board, "board"):
            board_array = state.board.board
        else:
            board_array = state.board

        return eval_board(board_array)

    def backpropagate(self, result):
        node = self
        while node is not None:
            node.visits += 1
            node.value += result
            node = node.parent

    def apply_move(self, state, move):
        try:
            new_state = GameState.from_node_or_state(state)
            board = new_state.board

            if hasattr(board, "move_piece"):
                # Handle ChessBoard object
                from_pos, to_pos = move
                success = board.move_piece(
                    from_pos[0], from_pos[1], to_pos[0], to_pos[1]
                )
                if not success:
                    return None
            else:
                # Handle list-based board
                from_pos, to_pos = move
                piece = board[from_pos[0]][from_pos[1]]
                if piece is None or piece.colour != state.player_turn:
                    return None

                # Create a deep copy of the board
                new_board = [[None for _ in range(8)] for _ in range(8)]
                for i in range(8):
                    for j in range(8):
                        if board[i][j] is not None:
                            new_piece = type(board[i][j])(board[i][j].colour)
                            if hasattr(board[i][j], "first_move"):
                                new_piece.first_move = board[i][j].first_move
                            new_board[i][j] = new_piece

                # Apply the move
                new_board[to_pos[0]][to_pos[1]] = new_board[from_pos[0]][from_pos[1]]
                new_board[from_pos[0]][from_pos[1]] = None
                if hasattr(new_board[to_pos[0]][to_pos[1]], "first_move"):
                    new_board[to_pos[0]][to_pos[1]].first_move = False

                new_state.board = new_board

            # Update player turn
            new_state.player_turn = (
                "black" if new_state.player_turn == "white" else "white"
            )
            return new_state

        except Exception as e:
            logging.error(f"Error applying move: {str(e)}")
            return None


class MCTS:
    def __init__(self, initial_state, iterations=1000, time_limit=None, is_white=True):
        self.root = Node(initial_state)
        self.iterations = iterations
        self.time_limit = time_limit
        self.is_white = is_white
        self.performance = {"iterations": 0, "time_taken": 0, "best_move": None}

    def run(self):
        if not self.root._untried_moves and not self.root.children:
            logging.info("No valid moves available")
            return None

        start_time = time.time()
        total_iterations = 0
        time_buffer = 0.1  # Buffer to ensure we don't exceed time limit

        def check_time():
            if self.time_limit is None:
                return False
            return (time.time() - start_time + time_buffer) >= self.time_limit

        try:
            while total_iterations < self.iterations:
                if check_time():
                    logging.info(
                        f"Time limit reached after {total_iterations} iterations"
                    )
                    break

                # Selection
                node = self.root
                while not node.is_terminal() and node.is_fully_expanded():
                    selected = node.select_child()
                    if selected is None:
                        break
                    node = selected

                # Expansion
                if not node.is_terminal():
                    expanded = node.expand()
                    if expanded != node:  # Only update if expansion was successful
                        node = expanded

                # Simulation
                result = node.simulate()

                # Backpropagation
                node.backpropagate(result)
                total_iterations += 1

            # Ensure at least one iteration completes if possible
            if total_iterations == 0 and not self.root.is_terminal():
                node = self.root.expand()
                if node != self.root:  # Only if expansion was successful
                    result = node.simulate()
                    node.backpropagate(result)
                    total_iterations = 1

        except Exception as e:
            logging.error(f"Error during MCTS: {str(e)}")
            return None

        end_time = time.time()
        self.performance["iterations"] = total_iterations
        self.performance["time_taken"] = end_time - start_time

        # Select best move
        if len(self.root.children) == 0:
            if len(self.root._untried_moves) > 0:
                # If we have untried moves but no children, return a random untried move
                move = random.choice(self.root._untried_moves)
                self.performance["best_move"] = move
                return move
            return None

        # Select child with most visits
        best_child = max(self.root.children, key=lambda c: c.visits)
        best_move = best_child.move_from_parent
        self.performance["best_move"] = best_move

        return best_move

    def best_uct(self, state):
        children = self.nodes[state]["children"]
        log_N = math.log(self.nodes[state]["visits"])
        return max(children, key=lambda child: self.uct_value(state, child, log_N))

    def uct_value(self, parent, child, log_N):
        node = self.nodes[child]
        return node["reward"] / node["visits"] + self.exploration_weight * math.sqrt(
            log_N / node["visits"]
        )

    def prune(self):
        # Implement node pruning logic here
        pass


# Example usage
initial_board_array = [[None for _ in range(8)] for _ in range(8)]

# Create white pieces
initial_board_array[0][0] = Rook("white")
initial_board_array[0][1] = Knight("white")
initial_board_array[0][2] = Bishop("white")
initial_board_array[0][4] = Queen("white")
initial_board_array[0][3] = King("white")
initial_board_array[0][5] = Bishop("white")
initial_board_array[0][6] = Knight("white")
initial_board_array[0][7] = Rook("white")
for i in range(8):
    initial_board_array[1][i] = Pawn("white")

# Create black pieces
initial_board_array[7][0] = Rook("black")
initial_board_array[7][1] = Knight("black")
initial_board_array[7][2] = Bishop("black")
initial_board_array[7][4] = Queen("black")
initial_board_array[7][3] = King("black")
initial_board_array[7][5] = Bishop("black")
initial_board_array[7][6] = Knight("black")
initial_board_array[7][7] = Rook("black")
for i in range(8):
    initial_board_array[6][i] = Pawn("black")
