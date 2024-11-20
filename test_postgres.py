import pytest
from postgres_auth import DBConnector


@pytest.fixture(scope="module")
def db():
    db = DBConnector()
    db.create_users_table()
    db.create_logins_table()
    yield db
    db._disconnect()


def test_create_users_table(db):
    db.create_users_table()
    db.cursor.execute("SELECT * FROM users")
    assert db.cursor.description is not None


def test_insert_user(db):
    db.insert_user("testuser", "password123")
    db.cursor.execute("SELECT * FROM users WHERE username = 'testuser'")
    user = db.cursor.fetchone()
    assert user is not None
    assert user[1] == "testuser"


def test_verify_user(db):
    db.insert_user("verifyuser", "password123")
    assert db.verify_user("verifyuser", "password123") is True
    assert db.verify_user("verifyuser", "wrongpassword") is False


def test_create_logins_table(db):
    db.create_logins_table()
    db.cursor.execute("SELECT * FROM logins")
    assert db.cursor.description is not None


def test_insert_login_attempt(db):
    db.insert_login_attempt("testuser", 123.45)
    db.cursor.execute("SELECT * FROM logins WHERE username = 'testuser'")
    login = db.cursor.fetchone()
    assert login is not None
    assert login[1] == "testuser"
    assert float(login[2]) == 123.45


def test_get_login_attempts(db):
    db.insert_login_attempt("testuser", 123.45)
    attempts = db.get_login_attemps("testuser")
    assert len(attempts) > 0
    assert attempts[0][0] == "testuser"
    assert float(attempts[0][1]) == 123.45
