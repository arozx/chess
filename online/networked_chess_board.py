import asyncio
import websockets
import pickle
import logging
import os

from chess_board_1 import ChessBoard


class NetworkedChessBoard(ChessBoard):
    def __init__(self, host="localhost", port=None, is_server=False):
        super().__init__()
        self.is_server = is_server
        self.host = host
        self.port = port if port is not None else int(os.getenv("PORT", 5556))
        self.websocket = None
        self.loop = asyncio.get_event_loop()
        self.recv_lock = asyncio.Lock()
        if is_server:
            self.loop.run_until_complete(self.start_server())
        else:
            self.loop.run_until_complete(self.connect_to_server())

    async def start_server(self):
        server = await websockets.serve(self.handle_connection, self.host, self.port)
        logging.info(f"Server started at {self.host}:{self.port}")
        await server.wait_closed()

    async def connect_to_server(self):
        self.websocket = await websockets.connect(f"ws://{self.host}:{self.port}")
        logging.info(f"Client connected to {self.host}:{self.port}")
        asyncio.ensure_future(self.receive_data())

    async def handle_connection(self, websocket):
        self.websocket = websocket
        asyncio.ensure_future(self.receive_data())

    def move_piece(self, x, y, endx, endy):
        if super().move_piece(x, y, endx, endy):
            self.loop.run_until_complete(self.send_move((x, y, endx, endy)))
            return True
        return False

    async def send_move(self, move):
        data = pickle.dumps(move)
        await self.websocket.send(data)

    async def receive_data(self):
        while True:
            async with self.recv_lock:
                try:
                    data = await self.websocket.recv()
                    move = pickle.loads(data)
                    super().move_piece(*move)
                except Exception as e:
                    logging.error(f"Error: {e}")
                    break
