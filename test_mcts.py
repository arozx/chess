import unittest
from mcts import Node, MCTS
from pieces import Rook, Knight, Bishop, Queen, King, Pawn


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
        self.mcts = MCTS(self.root_node, iterations=10, is_white=1)

    def test_node_initialization(self):
        node = Node(self.initial_board_array)
        self.assertEqual(node.board_array, self.initial_board_array)
        self.assertIsNone(node.move)
        self.assertIsNone(node.parent)
        self.assertEqual(node.children, [])
        self.assertEqual(node.visits, 0)
        self.assertEqual(node.value, 0)

    def test_node_is_leaf(self):
        node = Node(self.initial_board_array)
        self.assertTrue(node.is_leaf())
        node.children.append(Node(self.initial_board_array))
        self.assertFalse(node.is_leaf())

    def test_node_expand(self):
        node = Node(self.initial_board_array)
        all_valid_moves = [((1, 0), (2, 0)), ((1, 1), (2, 1))]
        node.expand(all_valid_moves)
        self.assertEqual(len(node.children), 2)

    def test_node_apply_move(self):
        node = Node(self.initial_board_array)
        move = ((1, 0), (2, 0))
        new_board_array = node.apply_move(self.initial_board_array, move)
        self.assertIsNotNone(new_board_array)
        self.assertIsNone(new_board_array[1][0])
        self.assertIsInstance(new_board_array[2][0], Pawn)

    def test_node_update(self):
        node = Node(self.initial_board_array)
        node.update(1)
        self.assertEqual(node.visits, 1)
        self.assertEqual(node.value, 1)

    def test_mcts_select(self):
        leaf = self.mcts.select(self.root_node)
        self.assertIsNotNone(leaf)

    def test_mcts_expand(self):
        self.mcts.expand(self.root_node)
        self.assertGreater(len(self.root_node.children), 0)

    def test_mcts_simulate(self):
        value = self.mcts.simulate(self.root_node)
        self.assertIsInstance(value, float)

    def test_mcts_backpropagate(self):
        leaf = self.mcts.select(self.root_node)
        self.mcts.backpropagate(leaf, 1)
        self.assertGreater(self.root_node.visits, 0)
        self.assertGreater(self.root_node.value, 0)

    def test_mcts_run(self):
        self.mcts.run()
        self.assertGreater(self.root_node.visits, 0)

    def test_mcts_best_move(self):
        self.mcts.run()
        best_move = self.mcts.best_move()
        self.assertIsNotNone(best_move)


if __name__ == "__main__":
    unittest.main()
