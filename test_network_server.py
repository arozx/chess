import socket
from unittest.mock import patch, MagicMock
from online.network_server import ChessServer


@patch("online.network_server.NetworkedChessBoard")
@patch("online.network_server.socket.socket")
@patch("online.network_server.ThreadPoolExecutor")
def test_chess_server_init(mock_executor, mock_socket, mock_chess_board):
    mock_socket_instance = MagicMock()
    mock_socket.return_value = mock_socket_instance

    server = ChessServer(host="localhost", port=5556, max_workers=5)

    # Check if NetworkedChessBoard is initialized correctly
    mock_chess_board.assert_called_once_with(
        host="localhost", port=5556, is_server=True
    )

    # Check if socket is created and configured correctly
    mock_socket.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)
    mock_socket_instance.setsockopt.assert_called_once_with(
        socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
    )
    mock_socket_instance.settimeout.assert_called_once_with(5)
    mock_socket_instance.bind.assert_called_once_with(("localhost", 5556))
    mock_socket_instance.listen.assert_called_once_with(5)

    # Check if ThreadPoolExecutor is initialized correctly
    mock_executor.assert_called_once_with(max_workers=5)

    # Check if clients list is initialized correctly
    assert server.clients == []

    # Check if logging info is called
    with patch("online.network_server.logging.info") as mock_logging_info:
        server = ChessServer(host="localhost", port=5556, max_workers=5)
        mock_logging_info.assert_called_once_with(
            "Server started, waiting for connections..."
        )
