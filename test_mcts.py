import unittest
from mcts import Node, MCTS
from pieces import Rook, Knight, Bishop, Queen, King, Pawn
from game_state import GameState


class TestMCTS(unittest.TestCase):
    def setUp(self):
        self.initial_board_array = [[None for _ in range(8)] for _ in range(8)]

        # Create white pieces
        self.initial_board_array[0][0] = Rook("white")
        self.initial_board_array[0][1] = Knight("white")
        self.initial_board_array[0][2] = Bishop("white")
        self.initial_board_array[0][4] = Queen("white")
        self.initial_board_array[0][3] = King("white")
        self.initial_board_array[0][5] = Bishop("white")
        self.initial_board_array[0][6] = Knight("white")
        self.initial_board_array[0][7] = Rook("white")
        for i in range(8):
            self.initial_board_array[1][i] = Pawn("white")

        # Create black pieces
        self.initial_board_array[7][0] = Rook("black")
        self.initial_board_array[7][1] = Knight("black")
        self.initial_board_array[7][2] = Bishop("black")
        self.initial_board_array[7][4] = Queen("black")
        self.initial_board_array[7][3] = King("black")
        self.initial_board_array[7][5] = Bishop("black")
        self.initial_board_array[7][6] = Knight("black")
        self.initial_board_array[7][7] = Rook("black")
        for i in range(8):
            self.initial_board_array[6][i] = Pawn("black")

        self.root_node = Node(self.initial_board_array)
        self.mcts = MCTS(self.initial_board_array, iterations=1000, is_white=True)

    def test_node_initialization(self):
        node = Node(self.initial_board_array)
        self.assertIsInstance(node.state, GameState)
        self.assertIsNone(node.parent)
        self.assertEqual(node.children, [])
        self.assertEqual(node.visits, 0)
        self.assertEqual(node.value, 0)
        self.assertIsNotNone(node._untried_moves)

    def test_node_expand(self):
        node = Node(self.initial_board_array)
        expanded_node = node.expand()
        self.assertIsNotNone(expanded_node)
        self.assertEqual(len(node.children), 1)
        self.assertIsNotNone(expanded_node.move_from_parent)

    def test_node_apply_move(self):
        node = Node(self.initial_board_array)
        move = ((1, 0), (2, 0))  # Move white pawn forward
        new_state = node.apply_move(node.state, move)
        self.assertIsNotNone(new_state)
        self.assertIsNone(new_state.board[1][0])  # Original position should be empty
        self.assertIsInstance(
            new_state.board[2][0], Pawn
        )  # New position should have pawn
        self.assertEqual(new_state.board[2][0].colour, "white")  # Should be white pawn

    def test_node_backpropagate(self):
        node = Node(self.initial_board_array)
        child = Node(self.initial_board_array, parent=node)
        node.children.append(child)
        child.backpropagate(1.0)
        self.assertEqual(node.visits, 1)
        self.assertEqual(node.value, 1.0)


if __name__ == "__main__":
    unittest.main()
