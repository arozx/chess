import os

import pytest

from db_connector import DBConnector

@pytest.fixture
def db():
    db_path = "/tmp/test_db.sqlite"
    connector = DBConnector(db_path)
    yield connector
    connector._disconnect()
    os.remove(db_path)


def test_create_users_table(db):
    db.create_users_table()
    db.cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
    )
    assert db.cursor.fetchone() is not None


def test_insert_user(db):
    db.create_users_table()
    db.insert_user("test_user", "password123")
    db.cursor.execute("SELECT * FROM users WHERE username='test_user'")
    user = db.cursor.fetchone()
    assert user is not None
    assert user[1] == "test_user"


def test_verify_user(db):
    db.create_users_table()
    db.insert_user("test_user", "password123")
    assert db.verify_user("test_user", "password123") is True
    assert db.verify_user("test_user", "wrongpassword") is False


def test_create_logins_table(db):
    db.create_logins_table()
    db.cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='logins'"
    )
    assert db.cursor.fetchone() is not None


def test_insert_login_attempt(db):
    db.create_logins_table()
    db.insert_login_attempt("test_user", 123.456)
    db.cursor.execute("SELECT * FROM logins WHERE username='test_user'")
    login = db.cursor.fetchone()
    assert login is not None
    assert login[1] == "test_user"
    assert login[2] == 123.46


def test_get_login_attempts(db):
    db.create_logins_table()
    db.insert_login_attempt("test_user", 123.456)
    attempts = db.get_login_attemps("test_user")
    assert len(attempts) == 1
    assert attempts[0][0] == "test_user"
    assert attempts[0][1] == 123.46


def test_create_games_table(db):
    db.create_games_table()
    db.cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='games'"
    )
    assert db.cursor.fetchone() is not None


def test_insert_game(db):
    db.create_games_table()
    db.insert_game("player1", "player2", "some_fen")
    db.cursor.execute(
        "SELECT * FROM games WHERE player1='player1' AND player2='player2'"
    )
    game = db.cursor.fetchone()
    assert game is not None
    assert game[1] == "player1"
    assert game[2] == "player2"
    assert game[3] == "some_fen"
