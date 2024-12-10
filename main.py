import pickle
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from online.networked_chess_board import NetworkedChessBoard

app = FastAPI()

# Initialize the chessboard globally
chess_board = NetworkedChessBoard(is_server=True)

# Set up logging
logging.basicConfig(level=logging.INFO)

# Add CORS Middleware to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)


@app.on_event("startup")
async def startup_event():
    """
    This will be called when FastAPI starts.
    """
    logging.info("ChessBoard server is starting...")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logging.info("WebSocket connection established")

    try:
        while True:
            data = await websocket.receive_bytes()  # Receive bytes
            move = pickle.loads(data)  # Deserialize the move
            if chess_board.move_piece(*move):  # Execute the move
                response = pickle.dumps(move)  # Serialize the move
                await websocket.send_bytes(
                    response
                )  # Send the response back to the client
                logging.info(f"Move executed: {move}")
            else:
                logging.warning(f"Failed to execute move: {move}")

    except WebSocketDisconnect:
        logging.info("WebSocket disconnected")

    except Exception as e:
        logging.error(f"WebSocket error: {e}")
