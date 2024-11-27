import socket
import sys


def check_health(host, port):
    try:
        with socket.create_connection((host, port), timeout=10):
            return True
    except Exception as e:
        print(f"Health check failed: {e}")
        return False


if __name__ == "__main__":
    host = "127.0.0.1"
    port = 5556
    if check_health(host, port):
        sys.exit(0)
    else:
        sys.exit(1)
