import os
import pytest
import hashlib

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
def test_db_connector_init(mock_connect):
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn

    db_connector = DBConnector(False)

    mock_connect.assert_called_once_with(
        dbname="userauth", user="postgres", host="localhost", password=""
    )
    assert db_connector.conn == mock_conn
    assert db_connector.cursor == mock_conn.cursor()


@patch("psycopg2.connect")
def test_create_users_table(mock_connect):
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn

    db_connector = DBConnector()
    db_connector.create_users_table()

    # Get the actual SQL query that was called
    actual_sql = mock_conn.cursor().execute.call_args[0][0]

    # Remove extra whitespace and compare
    expected_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id serial PRIMARY KEY,
            username TEXT,
            password_hash TEXT,
            salt TEXT,
            UNIQUE(salt, username)
        )"""

    assert " ".join(actual_sql.split()) == " ".join(expected_sql.split())


@patch("psycopg2.connect")
def test_insert_user(mock_connect):
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn

    db_connector = DBConnector()
    db_connector.insert_user("test_user", "test_password")

    mock_conn.cursor().execute.assert_called()
    mock_conn.commit.assert_called()


@patch("psycopg2.connect")
def test_verify_user(mock_connect):
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn
    mock_cursor = mock_conn.cursor()
    mock_cursor.fetchone.return_value = (
        hashlib.sha256(("test_password" + "test_salt").encode()).hexdigest(),
        "test_salt",
    )

    db_connector = DBConnector()
    result = db_connector.verify_user("test_user", "test_password")

    assert result is True


@patch("psycopg2.connect")
def test_create_logins_table(mock_connect):
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn

    db_connector = DBConnector()
    db_connector.create_logins_table()

    # Get the actual SQL query that was called
    actual_sql = mock_conn.cursor().execute.call_args[0][0]

    # Remove extra whitespace and compare
    expected_sql = """
        CREATE TABLE IF NOT EXISTS logins (
            id serial PRIMARY KEY,
            username TEXT,
            time numeric
        )"""

    assert " ".join(actual_sql.split()) == " ".join(expected_sql.split())


@patch("psycopg2.connect")
def test_insert_login_attempt(mock_connect):
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn

    db_connector = DBConnector()
    db_connector.insert_login_attempt("test_user", 123.456)

    mock_conn.cursor().execute.assert_called()
    mock_conn.commit.assert_called()


@patch("psycopg2.connect")
def test_get_login_attempts(mock_connect):
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn
    mock_cursor = mock_conn.cursor()
    mock_cursor.fetchall.return_value = [("test_user", 123.45)]

    db_connector = DBConnector()
    result = db_connector.get_login_attemps("test_user")

    assert result == [("test_user", 123.45)]
