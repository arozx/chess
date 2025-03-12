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

from pieces import Bishop, King, Knight, Pawn, Queen, Rook
from eval_board import eval_board
from game_state import GameState

# Get logger
logger = get_logger(__name__)

class Node:
    def __init__(self, state, move=None, parent=None):
        self.state = state if isinstance(state, GameState) else GameState(state)
        self.move = move
        self.parent = parent
        self.children = []
        self.visits = 0
        self.value = 0

    def is_leaf(self):
        return len(self.children) == 0

    def expand(self, all_valid_moves):
        for move in all_valid_moves:
            new_board_array = self.apply_move(self.state.board, move)
            if new_board_array:
                child = Node(new_board_array, move, self)
                self.children.append(child)

    def apply_move(self, board_array, move):
        new_board_array = copy.deepcopy(board_array)
        from_square, to_square = move

        try:
            piece = new_board_array[from_square[0]][from_square[1]]
            if piece is None or from_square == to_square:
                return None

            new_board_array[to_square[0]][to_square[1]] = piece
            new_board_array[from_square[0]][from_square[1]] = None

            return GameState(
                new_board_array,
                "black" if self.state.player_turn == "white" else "white",
            )
        except (IndexError, AttributeError):
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
        time_limit=None,
        is_white=True,
    ):
        self.game = game
        self.iterations = iterations
        self.exploration_weight = exploration_weight
        self.time_limit = time_limit
        self.is_white = is_white
        self.nodes = {}
        self.root = None

    def run(self):
        """
        Execute the MCTS algorithm from the root node.
        Returns the best move found.
        """
        start_time = time.time()

        # Initialize root with current game state
        initial_state = GameState(
            self.game.chess_board.board,
            "black" if not self.is_white else "white",  # Ensure correct player turn
        )

        logger.info(f"MCTS running for {'white' if self.is_white else 'black'} player")
        logger.info(f"Root state player turn: {initial_state.player_turn}")
        self.root = Node(initial_state)

        # Explicitly get legal moves and expand the root node first
        root_legal_moves = self.game.get_legal_moves(self.root.state)
        logger.info(f"Found {len(root_legal_moves)} legal moves for root node")

        # Directly create child nodes for the root
        for move in root_legal_moves:
            try:
                new_state = self.game.apply_move(self.root.state, move)
                if new_state:
                    child = Node(new_state, move, self.root)
                    self.root.children.append(child)
                    logger.debug(f"Added child for move {move}")
            except Exception as e:
                logger.error(f"Error adding child for move {move}: {e}")

        logger.info(f"Root now has {len(self.root.children)} children")

        if not self.root.children:
            logger.warning(
                "Failed to add any children to root. Debugging move application:"
            )
            # Try to debug the first few moves
            for i, move in enumerate(root_legal_moves[:5]):
                try:
                    source, target = move
                    source_row, source_col = source
                    target_row, target_col = target
                    piece = self.game.chess_board.board[source_row][source_col]
                    logger.debug(f"Testing move {i}: {move}")
                    logger.debug(
                        f"Piece at source: {piece.__class__.__name__ if piece else 'None'}"
                    )
                    logger.debug(f"Piece color: {piece.colour if piece else 'N/A'}")
                    logger.debug(f"Current player turn: {self.root.state.player_turn}")

                    # Verify that the piece belongs to the current player
                    if piece and piece.colour == self.root.state.player_turn:
                        logger.debug(f"Move {i} has correct piece color")
                    else:
                        logger.debug(f"Move {i} has WRONG piece color!")
                except Exception as e:
                    logger.error(f"Error debugging move {i}: {e}")

        # Continue with the MCTS algorithm
        for i in range(self.iterations):
            if self.time_limit and time.time() - start_time > self.time_limit:
                break

            # Select a leaf node
            leaf = self.select(self.root)

            # Expand the leaf node if it's not terminal and not already expanded
            if not leaf.is_leaf() and not self.game.is_terminal(leaf.state):
                moves = self.game.get_legal_moves(leaf.state)
                for move in moves:
                    new_state = self.game.apply_move(leaf.state, move)
                    if new_state:
                        child = Node(new_state, move, leaf)
                        leaf.children.append(child)

            # Select a random child if available
            simulation_leaf = leaf
            if leaf.children:
                simulation_leaf = random.choice(leaf.children)

            # Simulate a random game from this position
            reward = self.simulate(simulation_leaf)

            # Backpropagate the result
            self.backpropagate(simulation_leaf, reward)

        return self.best_move()

    def best_move(self):
        """
        Find the best move among the children of the root node
        """
        if not self.root or not self.root.children:
            logger.warning("No children in the root node")
            logger.debug(
                f"Root state player turn: {self.root.state.player_turn if self.root else 'None'}"
            )
            logger.debug(
                f"Children count: {len(self.root.children) if self.root else 'None'}"
            )
            return None

        # Print all children and their visit counts for debugging
        logger.info(f"Root has {len(self.root.children)} children:")
        for i, child in enumerate(self.root.children):
            logger.debug(
                f"Child {i}: Move {child.move}, Visits {child.visits}, Value {child.value}"
            )

        # Choose the child with the highest visit count
        if self.root.children:
            best_child = max(self.root.children, key=lambda c: c.visits)
            logger.info(
                f"Best child: Move {best_child.move}, Visits {best_child.visits}, Value {best_child.value}"
            )
            return best_child.move
        return None

    def search(self, state):
        start_time = time.time()
        for _ in range(self.iterations):
            if self.time_limit and time.time() - start_time > self.time_limit:
                break
            self.simulate(state)

    def select(self, node):
        """
        Select a leaf node using UCT.
        Returns the selected node, not a path.
        """
        current = node
        while not current.is_leaf():
            # Choose the best child according to UCT
            best_value = float("-inf")
            best_child = None

            for child in current.children:
                if child.visits == 0:
                    return child  # Select unexplored node first

                # UCT formula
                exploit = child.value / child.visits
                explore = self.exploration_weight * math.sqrt(
                    2 * math.log(current.visits) / child.visits
                )
                uct_value = exploit + explore

                if uct_value > best_value:
                    best_value = uct_value
                    best_child = child

            if best_child is None:
                return current
            current = best_child

        return current

    def simulate(self, node):
        """
        Run a simulation from the node's state to a terminal position,
        then return the reward.
        """
        try:
            # Always use the node's state, not the node itself
            current_state = node.state
            depth = 0
            max_depth = 30  # Reduce to prevent excessive computation

            while depth < max_depth:
                try:
                    # Check terminal state with a try/except to handle errors
                    terminal = False
                    try:
                        terminal = self.game.is_terminal(current_state)
                    except Exception as e:
                        logger.error(f"Error checking terminal state: {e}")
                        break

                    if terminal:
                        break

                    legal_moves = []
                    try:
                        legal_moves = self.game.get_legal_moves(current_state)
                    except Exception as e:
                        logger.error(f"Error getting legal moves: {e}")
                        break

                    if not legal_moves:
                        break

                    move = random.choice(legal_moves)
                    new_state = None
                    try:
                        new_state = self.game.apply_move(current_state, move)
                    except Exception as e:
                        logger.error(f"Error applying move: {e}")
                        break

                    if not new_state:
                        break

                    current_state = new_state
                    depth += 1

                except Exception as e:
                    logger.error(f"Error in simulation loop: {e}")
                    break

            # Calculate reward carefully with exception handling
            try:
                if hasattr(self.game, "get_reward"):
                    return self.game.get_reward(current_state, self.is_white)
                else:
                    return (
                        eval_board(
                            current_state.board,
                            "white" if self.is_white else "black",
                            score_normalised=False,
                        )
                        / 100.0
                    )
            except Exception as e:
                logger.error(f"Error calculating reward: {e}")
                return 0.0

        except Exception as e:
            logger.error(f"Global simulation error: {e}")
            return 0.0  # Safe default

    def expand(self, state):
        if state in self.nodes:
            return
        self.nodes[state] = {
            "children": self.game.get_legal_moves(state),
            "unexplored": set(self.game.get_legal_moves(state)),
            "visits": 0,
            "reward": 0,
        }

    def backpropagate(self, node, reward):
        """
        Backpropagate the reward from the leaf node to the root.
        """
        while node:
            node.visits += 1
            node.value += reward
            node = node.parent

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
