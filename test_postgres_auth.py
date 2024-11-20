import os
import pytest
from unittest.mock import patch, MagicMock
from postgres_auth import DBConnector


@pytest.fixture
def mock_env_vars():
    with patch.dict(
        os.environ,
        {
            "DB_NAME": "userauth",
            "DB_USER": "postgres",
            "DB_HOST": "localhost",
            "DB_PASSWORD": "",
        },
    ):
        yield


@patch("psycopg2.connect")
def test_db_connector_init(mock_connect, mock_env_vars):
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn

    db_connector = DBConnector()

    mock_connect.assert_called_once_with(
        dbname="userauth", user="postgres", host="localhost", password=""
    )
    assert db_connector.conn == mock_conn
    assert db_connector.cursor == mock_conn.cursor()
