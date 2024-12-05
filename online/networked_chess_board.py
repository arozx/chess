import threading
import socket
import pickle
import logging


from chess_board_1 import ChessBoard


class NetworkedChessBoard(ChessBoard):
    def __init__(self, host="localhost", port=5556, is_server=False):
        super().__init__()
        self.is_server = is_server
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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

            # listening loop
            while True:
                try:
                    self.socket.listen(1)
                    logging.info("Server listening for connections...")
                    self.client_socket, _ = self.socket.accept()
                    self.receive_thread = threading.Thread(target=self.receive_data)
                    self.receive_thread.start()
                except Exception as e:
                    print(e)
        else:
            self.socket.connect((host, port))
            logging.info(f"Client connected to {host}:{port}")
            self.client_socket = self.socket
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
                data = self.client_socket.recv(4096)
                if not data:
                    break
                move = pickle.loads(data)
                super().move_piece(*move)
            except socket.timeout:
                continue
            except Exception as e:
                logging.error(f"Error: {e}")
                break
