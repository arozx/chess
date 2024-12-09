import asyncio
import pickle
import logging

import websockets

from online.networked_chess_board import NetworkedChessBoard


class ChessServer:
    def __init__(self, host="localhost", port=5556):
        self.uri = f"ws://{host}:{port}"
        self.chess_board = NetworkedChessBoard(is_server=True)
        self.clients = set()

    async def handler(self, websocket):
        self.clients.add(websocket)
        try:
            async for message in websocket:
                move = pickle.loads(message)
                if self.chess_board.move_piece(*move):
                    await self.broadcast(pickle.dumps(move))
        except Exception as e:
            logging.error(f"Client error: {e}")
        finally:
            self.clients.remove(websocket)

    async def broadcast(self, data):
        for client in self.clients:
            try:
                await client.send(data)
            except Exception as e:
                logging.error(f"Broadcast error: {e}")

    async def start(self, host, port):
        async with websockets.serve(self.handler, host, port):
            logging.info(f"Server started on {host}:{port}")
            await asyncio.Future()  # Run forever


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    server = ChessServer()
    asyncio.run(server.start("localhost", 5556))
