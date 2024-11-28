import pytest
import tempfile

from db_connector import SQLiteDBConnector

@pytest.fixture
def db():
    with tempfile.NamedTemporaryFile(suffix=".sqlite") as temp_db:
        db_path = temp_db.name
        connector = SQLiteDBConnector(db_path)
        yield connector
        connector._disconnect()


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
