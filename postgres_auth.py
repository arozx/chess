import psycopg2
import hashlib
import dotenv
import os


class DBConnector:
    def __init__(self, env=True):
        if env:
            dotenv.load_dotenv()
            # load vars
            self.DB_NAME = os.getenv("DB_NAME")
            self.DB_USER = os.getenv("DB_USER")
            self.DB_HOST = os.getenv("DB_HOST")
            self.DB_PASSWORD = os.getenv("DB_PASSWORD")
        else:
            self.DB_NAME = "userauth"
            self.DB_USER = "postgres"
            self.DB_HOST = "localhost"
            self.DB_PASSWORD = ""

        # connect to the database
        self._connect()

    """
    Initiates connection to the database
    returns N/A
    """

    def _connect(self):
        self.conn = psycopg2.connect(
            dbname=self.DB_NAME,
            user=self.DB_USER,
            host=self.DB_HOST,
            password=self.DB_PASSWORD,
        )

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
            id serial PRIMARY KEY,
            username TEXT,
            password_hash TEXT,
            salt TEXT,
            UNIQUE(salt, username)
        )""")
        self.conn.commit()

    """
    Inserts a user
    Doesn't do any validation
    hashing is done inside the function
    returns N/A
    """

    def insert_user(self, username, password):
        salt = os.urandom(16).hex()
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        query = f"INSERT INTO users (username, password_hash, salt) VALUES ('{username}', '{password_hash}', '{salt}')"
        self.__execute_query(query)

    """
    Checks if a user is inside the database
    return N/A
    """

    def verify_user(self, username, password):
        query = f"SELECT password_hash, salt FROM users WHERE username = '{username}'"
        cursor = self.__execute_query(query)
        result = cursor.fetchone()
        if result:
            stored_hash, salt = result
            password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return stored_hash == password_hash
        return False

    """
    Table for user login times
    Stores ID and login times
    returns N/A
    """

    def create_logins_table(self):
        c = self.conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS logins (
            id serial PRIMARY KEY,
            username TEXT,
            time numeric
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


if __name__ == "__main__":
    db = DBConnector()
    db.create_users_table()
    db.create_logins_table()

    # create a user
    paswd = "jack2"
    user = "jack2"
    db.insert_user(user, paswd)
    print(db.verify_user(user, paswd))
