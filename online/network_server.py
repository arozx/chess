import socket
import pickle
import logging

from concurrent.futures import ThreadPoolExecutor

from online.networked_chess_board import NetworkedChessBoard


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

    def shutdown(self):
        for client in self.clients:
            try:
                client.close()
            except Exception as e:
                print(f"Error closing client connection: {e}")
        self.server.close()
        self.executor.shutdown(wait=True)

    def start(self):
        while True:
            client_socket, addr = self.server.accept()
            print(f"Connection from {addr}")
            self.clients.append(client_socket)
            self.executor.submit(self.handle_client, client_socket)


if __name__ == "__main__":
    server = ChessServer()
    server.start()
