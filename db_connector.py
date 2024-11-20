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
