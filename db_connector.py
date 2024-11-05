import hashlib
import sqlite3


class DBConnector:
    def __init__(self, database):
        self.database = database
        self._connect()

    """
    Initiates connection to the database
    returns N/A
    """

    def _connect(self):
        self.conn = sqlite3.connect(self.database)
        self.cursor = self.conn.cursor()
        self.conn.commit()

    """
    Disconnects the application from the database
    returns N/A
    """

    def _disconnect(self):
        if self.conn:
            self.conn.close()

    """
    executes SQLite queries
    returns cursor
    """

    def __execute_query(self, query):
        cursor = self.conn.cursor()
        cursor.execute(query)
        self.conn.commit()
        return cursor

    """
    Creates a users table if it doesn't exist
    returns N/A
    """

    def create_users_table(self):
        c = self.conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            password_hash TEXT
        )""")
        self.conn.commit()

    """
    Inserts a user
    Doesn't do any validation
    hashing is done inside the function
    returns N/A
    """

    def insert_user(self, username, password):
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        query = f"INSERT INTO users (username, password_hash) VALUES ('{username}', '{password_hash}')"
        self.__execute_query(query)

    """
    Checks if a user is inside the database
    return N/A
    """

    def verify_user(self, username, password):
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        query = f"SELECT * FROM users WHERE username = '{username}' AND password_hash = '{password_hash}'"
        cursor = self.__execute_query(query)
        return cursor.fetchone() is not None

    """
    Table for user login times
    Stores ID and login times
    returns N/A
    """

    def create_logins_table(self):
        c = self.conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS logins (
            id INTEGER PRIMARY KEY,
            username TEXT,
            time REAL
        )""")
        self.conn.commit()

    """
    Inserts login times for a givern username
    Time is rounded to 2 dp
    returns N/A
    """

    def insert_login_attempt(self, username, time):
        query = (
            f"INSERT INTO logins (username, time) VALUES('{username}', '{time:.2f}')"
        )
        self.__execute_query(query)

    """
    Retrive login attemps
    returns the attemps as an array if there are any
    returns N/A
    """

    def get_login_attemps(self, username):
        query = f"SELECT username, time FROM logins WHERE username = '{username}'"
        cursor = self.__execute_query(query)
        if cursor is not None:
            return cursor.fetchall()

    """
    Creates a table to store games
    Store game possitions as FEN
    returns N/A
    """

    def create_games_table(self):
        c = self.conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY,
                player1 TEXT,
                player2 TEXT,
                fen TEXT
            )
        """)
        self.conn.commit()

    """
    Adds game to the games table
    returns N/A
    """

    def insert_game(self, player1, player2, fen):
        query = f"INSERT INTO games (player1, player2, fen) VALUES ('{player1}', '{player2}', '{fen}')"
        self.__execute_query(query)
