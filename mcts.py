"""
mcts.py
This exists as a standalone component of a chess application
Uses a monte Carlo algorithm to generate moves with alpha beta pruning
The best move is returned as a array of tuples
"""

import math
import random
import copy

from pieces import Bishop, King, Knight, Pawn, Queen, Rook
from eval_board import eval_board

class Node:
    def __init__(self, board_array, move=None, parent=None):
        self.board_array = board_array
        self.move = move
        self.parent = parent
        self.children = []
        self.visits = 0
        self.value = 0

    def is_leaf(self):
        return len(self.children) == 0

    def expand(self, all_valid_moves):
        for move in all_valid_moves:
            new_board_array = self.apply_move(self.board_array, move)
            if new_board_array:
                child = Node(new_board_array, move, self)
                self.children.append(child)

    def apply_move(self, board_array, move):
        new_board_array = copy.deepcopy(board_array)
        from_square, to_square = move
        piece = new_board_array[from_square[0]][from_square[1]]

        # when the move is not possible
        if from_square == to_square:
            return None

        # end early if there is no piece on the square
        if piece is None:
            return None

        # Move the piece
        new_board_array[to_square[0]][to_square[1]] = piece
        new_board_array[from_square[0]][from_square[1]] = None

        return new_board_array

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
    def __init__(self, root, iterations=100, is_white=1):
        self.root = root
        self.iterations = iterations
        self.is_white = is_white

    def select(self, node):
        while not node.is_leaf():
            node = node.best_child(exploration_weight=1.4)
        return node

    def expand(self, node):
        all_valid_moves = self.get_all_valid_moves(node.board_array)
        node.expand(all_valid_moves)

    def simulate(self, node):
        print(node)
        board_array = node.board_array
        return eval_board(board_array, "black", True)

    def backpropagate(self, node, value):
        while node is not None:
            node.update(value)
            node = node.parent

    def run(self):
        for _ in range(self.iterations):
            leaf = self.select(self.root)
            self.expand(leaf)
            value = self.simulate(leaf)
            self.backpropagate(leaf, value)

    def get_all_valid_moves(self, board_array):
        valid_moves = []
        for x in range(8):
            for y in range(8):
                if board_array[x][y] is not None:
                    if self.is_white and board_array[x][y].colour == "white":
                        valid_moves = self.get_multiple_moves(
                            board_array, valid_moves, x, y
                        )
                    elif not self.is_white and board_array[x][y].colour == "black":
                        valid_moves = self.get_multiple_moves(
                            board_array, valid_moves, x, y
                        )
        return valid_moves

    def get_multiple_moves(self, board_array, valid_moves, x, y):
        moves = board_array[x][y].get_valid_moves(board_array, x, y)
        for move in moves:
            if move != (0, 0):
                valid_moves.append(((x, y), move))
        return valid_moves

    def best_move(self):
        best_child = max(self.root.children, key=lambda child: child.visits)
        return best_child.move


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
