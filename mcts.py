"""
mcts.py
This exists as a standalone component of a chess application
Uses a monte Carlo algorithm to generate moves with alpha beta pruning
The best move is returned as a array of tuples
"""

import math
import copy
import time
import random
from logging_config import get_logger
from performance_monitoring import (
    track_performance,
    measure_operation,
    track_slow_operations,
)

from pieces import Bishop, King, Knight, Pawn, Queen, Rook
from eval_board import eval_board
from game_state import GameState

# Get logger
logger = get_logger(__name__)

class Node:
    def __init__(self, state, move=None, parent=None):
        self.state = state
        self.move = move
        self.parent = parent
        self.children = []
        self.visits = 0
        self.value = 0

    def is_leaf(self):
        return len(self.children) == 0

    @track_performance(op="mcts", name="expand_node")
    def expand(self, all_valid_moves):
        for move in all_valid_moves:
            new_state = self.apply_move(self.state, move)
            if new_state:
                child = Node(new_state, move, self)
                self.children.append(child)

    @track_performance(op="mcts", name="apply_move")
    def apply_move(self, board, move):
        """Apply a move to a board state and return new board"""
        new_board = board.clone()
        from_square, to_square = move

        if new_board.move_piece(
            from_square[0], from_square[1], to_square[0], to_square[1]
        ):
            return new_board
        return None

    def update(self, value):
        self.visits += 1
        self.value += value

    def best_child(self, exploration_weight):
        best_value = float("-inf")
        best_child = None
        for child in self.children:
            if child.visits == 0:
                value = float("inf")
            else:
                value = child.value / child.visits + exploration_weight * math.sqrt(
                    2 * math.log(self.visits) / child.visits
                )
            if value > best_value:
                best_value = value
                best_child = child
        return best_child


class MCTS:
    def __init__(
        self,
        game,
        iterations=1000,
        exploration_weight=1.41,
        time_limit=5,
        is_white=True,
    ):
        self.game = game
        self.iterations = iterations
        self.exploration_weight = exploration_weight
        self.time_limit = time_limit
        self.is_white = is_white
        self.nodes = {}
        self.root = None
        self.start_time = None

    @track_performance(op="mcts", name="select_node")
    def select(self, node):
        while not node.is_leaf() and not self.game.is_terminal(node.state):
            if not node.children:
                break
            node = self.get_best_uct(node)
        return node

    @track_performance(op="mcts", name="expand")
    def expand(self, node):
        if not self.game.is_terminal(node.state):
            valid_moves = self.game.get_legal_moves(node.state)
            node.expand(valid_moves)

    @track_performance(op="mcts", name="simulate")
    def simulate(self, node):
        state = node.state.clone()
        depth = 0
        max_depth = 50  # Prevent infinite loops

        while not self.game.is_terminal(state) and depth < max_depth:
            valid_moves = self.game.get_legal_moves(state)
            if not valid_moves:
                break
            move = random.choice(valid_moves)
            new_state = self.game.apply_move(state, move)
            if new_state is None:
                break
            state = new_state
            depth += 1

        return self.game.get_reward(state, self.is_white)

    @track_performance(op="mcts", name="backpropagate")
    def backpropagate(self, node, reward):
        while node is not None:
            node.update(reward)
            node = node.parent

    def get_best_uct(self, node):
        exploration = 1.4
        best_score = float("-inf")
        best_child = None

        for child in node.children:
            if child.visits == 0:
                return child

            exploitation = child.value / child.visits
            exploration_term = exploration * math.sqrt(
                math.log(node.visits) / child.visits
            )
            uct_score = exploitation + exploration_term

            if uct_score > best_score:
                best_score = uct_score
                best_child = child

        return best_child

    @track_performance(op="mcts", name="get_best_move")
    def get_best_move(self, root):
        if not root.children:
            return None

        best_child = max(root.children, key=lambda c: c.visits)
        return best_child.move

    @track_performance(op="mcts", name="run_mcts")
    def run(self):
        with measure_operation(
            "mcts_search", "ai_processing", tags={"iterations": self.iterations}
        ) as span:
            self.start_time = time.time()
            root = Node(self.game.chess_board)

            for i in range(self.iterations):
                if time.time() - self.start_time > self.time_limit:
                    logger.info(f"MCTS stopped after {i} iterations due to time limit")
                    span.set_data("actual_iterations", i)
                    break

                with measure_operation(
                    "mcts_iteration", "ai_processing", tags={"iteration": i}
                ) as iteration_span:
                    selected_node = self.select(root)
                    self.expand(selected_node)

                    if selected_node.children:  # If expansion was successful
                        child = random.choice(selected_node.children)
                        reward = self.simulate(child)
                        self.backpropagate(child, reward)

            best_move = self.get_best_move(root)
            span.set_data("final_iterations", root.visits)
            span.set_data("best_move", str(best_move) if best_move else None)

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
