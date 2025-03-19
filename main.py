import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from online.networked_chess_board import NetworkedChessBoard
import json
import sys
from logging_config import configure_logging
from PyQt5.QtWidgets import QApplication
from gui import ChessBoardUI

import dotenv
import os
from contextlib import asynccontextmanager

# Configure logging first
logger = configure_logging()

# Try to import and initialize Sentry, but don't fail if not available
try:
    from sentry_config import init_sentry

    SENTRY_INITIALIZED = init_sentry()
except ImportError:
    logger.warning(
        "Sentry configuration not available. Error tracking will be disabled."
    )
    SENTRY_INITIALIZED = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dotenv.load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup/shutdown events"""
    logger.info("Starting up...")
    await startup_event()
    yield
    logger.info("Shutting down...")


# Create FastAPI app instance first
app = FastAPI(lifespan=lifespan)

# Then add middleware based on environment
match os.getenv("ENVIRONMENT"):
    case "production":
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "https://appori2n7.azurewebsites.net/",
                "http://appori2n7.azurewebsites.net/",
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    case "development":
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:8080", "https://localhost:8080"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    case _:
        logger.warning("Origins not configured using all origins")
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )


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


@app.get("/")
def read_root():
    return {"message": "Welcome to the Chess API"}


@app.get("/test", response_class=HTMLResponse)
def test():
    # return a simple html
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
    </head>
    <body>
        <h1>Hello, world!</h1>
        <p>This is a test page.</p>
    </body>
    </html>
    """


# Initialize the chessboard globally
chess_board = NetworkedChessBoard(is_server=True)


async def startup_event():
    """
    This will be called when FastAPI starts.
    """
    logging.info("ChessBoard server is starting...")
    try:
        # Add any startup checks here
        pass
    except Exception as e:
        logger.error(f"Startup error: {e}")
        if SENTRY_INITIALIZED:
            import sentry_sdk

            sentry_sdk.capture_exception(e)


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            logger.info(f"Received message: {message}")

            # Process the received message based on its type
            if message["type"] == "test":
                # Send test response immediately
                await manager.send_message(
                    client_id,
                    json.dumps({"type": "test_response", "message": "Test received"}),
                )
            elif message["type"] == "move":
                # Process move
                await manager.send_message(
                    client_id,
                    json.dumps({"type": "move_confirmed", "move": message["move"]}),
                )
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error: {e}")
        if SENTRY_INITIALIZED:
            import sentry_sdk

            sentry_sdk.capture_exception(e)
        manager.disconnect(client_id)


def main():
    """Main entry point for the application."""
    logger.info("Starting Chess Game Application")
    try:
        app = QApplication(sys.argv)
        window = ChessBoardUI()
        window.show()
        return app.exec_()
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}")
        if SENTRY_INITIALIZED:
            import sentry_sdk

            sentry_sdk.capture_exception(e)
        raise


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}")
        if SENTRY_INITIALIZED:
            import sentry_sdk

            sentry_sdk.capture_exception(e)
        logger.exception("Application crashed")
        sys.exit(1)
