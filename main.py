import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from online.networked_chess_board import NetworkedChessBoard
import json
import sys
from logging_config import configure_logging
from PyQt5.QtWidgets import QApplication
from gui import ChessBoardUI

# Configure logging
logger = configure_logging()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections = {}
        self.games = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected")

    async def send_message(self, client_id: str, message: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)


manager = ConnectionManager()


@app.get("/health")
def health_check():
    # check if db is healthy

    # check if chess engine is healthy

    return {"status": "healthy"}


@app.get("/")
def read_root():
    return {"message": "Welcome to the Chess API"}


# Initialize the chessboard globally
chess_board = NetworkedChessBoard(is_server=True)

@app.on_event("startup")
async def startup_event():
    """
    This will be called when FastAPI starts.
    """
    logging.info("ChessBoard server is starting...")

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            logger.info(f"Received message: {message}")

            # Process the received message based on its type
            if message["type"] == "move":
                # Process move
                # This is where you would integrate with your chess engine
                await manager.send_message(
                    client_id,
                    json.dumps({"type": "move_confirmed", "move": message["move"]}),
                )
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"Error: {e}")
        manager.disconnect(client_id)


def main():
    """Main entry point for the application."""
    logger.info("Starting Chess Game Application")
    app = QApplication(sys.argv)
    window = ChessBoardUI()
    window.show()
    return app.exec_()

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}")
        logger.exception("Application crashed")
        sys.exit(1)
