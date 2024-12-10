import asyncio
import logging
from chess_board_1 import ChessBoard


class NetworkedChessBoard(ChessBoard):
    def __init__(self, is_server=False):
        super().__init__()
        self.is_server = is_server
        self.server = None

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
