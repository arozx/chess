import threading
import socket
import pickle
import logging
from concurrent.futures import ThreadPoolExecutor

from chess_board_1 import ChessBoard


class NetworkedChessBoard(ChessBoard):
    def __init__(self, host="localhost", port=5556, is_server=False):
        super().__init__()
        self.is_server = is_server
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(5)  # Set a timeout for the socket
        if is_server:
            for _ in range(5):  # Retry up to 5 times
                try:
                    self.socket.bind((host, port))
                    logging.info(f"Server bound to {host}:{port}")
                    break
                except OSError as e:
                    if e.errno == 98:  # Address already in use
                        logging.warning(
                            f"Port {port} already in use, retrying with port {port + 1}"
                        )
                        port += 1
                    else:
                        raise
            self.socket.listen(1)
            logging.info("Server listening for connections...")
            self.client_socket, _ = self.socket.accept()
            logging.info("Client connected")
            self.client_socket.settimeout(5)  # Set a timeout for the client socket
            self.receive_thread = threading.Thread(target=self.receive_data)
            self.receive_thread.start()
        else:
            self.socket.connect((host, port))
            logging.info(f"Client connected to {host}:{port}")
            self.receive_thread = threading.Thread(target=self.receive_data)
            self.receive_thread.start()

    """
    Takes the piece and coordinates as arguments
    returns the status of the move
    """

    def move_piece(self, x, y, endx, endy):
        if super().move_piece(x, y, endx, endy):
            self.send_move((x, y, endx, endy))
            return True
        return False

    """
    Takes a move as an argument
    sends the move over the socket
    returns N/A
    """

    def send_move(self, move):
        data = pickle.dumps(move)
        if self.is_server:
            self.client_socket.send(data)
        else:
            self.socket.send(data)

    """
    Takes no arguments
    Listens for data
    Executes operations
    Returns N/A
    """

    def receive_data(self):
        while True:
            try:
                data = (
                    self.client_socket.recv(4096)
                    if self.is_server
                    else self.socket.recv(4096)
                )
                if not data:
                    break
                move = pickle.loads(data)
                super().move_piece(*move)
            except socket.timeout:
                continue
            except Exception as e:
                logging.error(f"Error: {e}")
                break


class ChessServer:
    def __init__(self, host="localhost", port=5556, max_workers=5):
        self.chess_board = NetworkedChessBoard(host=host, port=port, is_server=True)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.settimeout(5)  # Set a timeout for the server socket
        self.server.bind((host, port))
        self.server.listen(5)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.clients = []
        logging.info("Server started, waiting for connections...")

    def handle_client(self, client_socket):
        client_socket.settimeout(5)  # Set a timeout for the client socket
        while True:
            try:
                data = client_socket.recv(4096)
                if not data:
                    break
                move = pickle.loads(data)
                if self.chess_board.move_piece(*move):
                    self.broadcast(pickle.dumps(move))
            except socket.timeout:
                continue
            except Exception as e:
                logging.error(f"Error: {e}")
                break
        client_socket.close()

    def broadcast(self, data):
        for client in self.clients:
            try:
                client.sendall(data)
            except Exception as e:
                logging.error(f"Broadcast error: {e}")
