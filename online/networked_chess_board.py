import asyncio
import logging
import copy
from chess_board_1 import ChessBoard
from pieces import Pawn, Rook, Knight, Bishop, Queen, King


class NetworkedChessBoard(ChessBoard):
    def __init__(self, is_server=False):
        super().__init__()
        self.is_server = is_server
        self.server = None

    def __getitem__(self, key):
        """Make the board subscriptable for AI compatibility"""
        return self.board[key]

    def __iter__(self):
        """Make the board iterable for AI compatibility"""
        return iter(self.board)

    def clone(self):
        """Create a deep copy of the board for AI search"""
        new_board = NetworkedChessBoard(is_server=self.is_server)
        new_board.board = [[None for _ in range(8)] for _ in range(8)]

        # Deep copy each piece
        for i in range(8):
            for j in range(8):
                piece = self.board[i][j]
                if piece:
                    piece_type = type(piece)
                    new_piece = piece_type(piece.colour)
                    # Copy important piece attributes
                    if hasattr(piece, "first_move"):
                        new_piece.first_move = piece.first_move
                    new_board.board[i][j] = new_piece

        new_board.player_turn = self.player_turn
        new_board.move_count = self.move_count
        new_board.material = self.material  # Copy material score
        return new_board

    def get_valid_moves(self, x, y):
        """Get all valid moves for a piece at position (x,y)"""
        piece = self.board[x][y]
        if piece and piece.colour == self.player_turn:
            return piece.get_valid_moves(self.board, x, y)
        return []

    def game_over(self):
        """Check if the game is over"""
        # Check for checkmate
        if self.are_you_in_check(self.player_turn) == 2:
            return True

        # Check for stalemate (no valid moves but not in check)
        for x in range(8):
            for y in range(8):
                piece = self.board[x][y]
                if piece and piece.colour == self.player_turn:
                    if piece.get_valid_moves(self.board, x, y):
                        return False
        return True

    async def start_server(self, host="localhost", port=5556):
        """
        Starts a WebSocket server to handle chessboard communication.
        """
        self.server = await asyncio.start_server(self.handle_client, host, port)
        logging.info(f"Server running on {host}:{port}")
        async with self.server:
            await self.server.serve_forever()

    async def handle_client(self, reader, writer):
        """
        Handles communication with a client.
        """
        while True:
            try:
                data = await reader.read(100)
                if not data:
                    break
                # Handle data (e.g., process moves)
                logging.info(f"Received: {data}")
            except Exception as e:
                logging.error(f"Error handling client: {e}")
                break
        writer.close()
        await writer.wait_closed()
