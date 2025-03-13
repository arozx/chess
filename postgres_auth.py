import psycopg2
import psycopg2.pool
import hashlib
import dotenv
import os
import sentry_sdk
from logging import getLogger
import time
from sentry_sdk import configure_scope, set_tag

logger = getLogger(__name__)


class DBConnector:
    def __init__(self, env=True):
        try:
            # Set database context for Sentry
            with configure_scope() as scope:
                scope.set_tag("database.connection", "initializing")

            if env:
                dotenv.load_dotenv()
                # Use Neon's connection URL
                self.DATABASE_URL = os.getenv("DATABASE_URL")
                if not self.DATABASE_URL:
                    # Fallback to individual connection parameters if DATABASE_URL not set
                    self.DB_NAME = os.getenv("DB_NAME")
                    self.DB_USER = os.getenv("DB_USER")
                    self.DB_HOST = os.getenv("DB_HOST")
                    self.DB_PASSWORD = os.getenv("DB_PASSWORD")
                    self.DATABASE_URL = f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}/{self.DB_NAME}"
            else:
                self.DATABASE_URL = "postgresql://postgres@localhost/userauth"

            # Update database context
            with configure_scope() as scope:
                scope.set_tag(
                    "database.url", self.DATABASE_URL.split("@")[-1]
                )  # Only log host/db, not credentials

            # Create connection pool
            self.pool = psycopg2.pool.SimpleConnectionPool(1, 10, self.DATABASE_URL)
            if not self.pool:
                raise Exception("Failed to create connection pool")

            # Get initial connection to verify everything works
            self.conn = self.pool.getconn()
            self.cursor = self.conn.cursor()

            # Set successful connection tag
            with configure_scope() as scope:
                scope.set_tag("database.connection", "connected")

        except Exception as e:
            with configure_scope() as scope:
                scope.set_tag("database.connection", "failed")
            logger.error(f"Failed to initialize database connection: {e}")
            sentry_sdk.capture_exception(e)
            raise

    """
    Initiates connection to the database
    returns N/A
    """

    def _connect(self):
        try:
            with sentry_sdk.start_span(
                op="db.connect", description="Get connection from pool"
            ) as span:
                if not self.conn or self.conn.closed:
                    self.conn = self.pool.getconn()
                    self.cursor = self.conn.cursor()
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            sentry_sdk.capture_exception(e)
            raise

    """
    Disconnects the application from the database
    returns N/A
    """

    def _disconnect(self):
        try:
            if self.conn and not self.conn.closed:
                self.cursor.close()
                self.pool.putconn(self.conn)
                self.conn = None
                self.cursor = None
        except Exception as e:
            logger.error(f"Error disconnecting from database: {e}")
            sentry_sdk.capture_exception(e)
        finally:
            try:
                if self.pool:
                    self.pool.closeall()
            except Exception as e:
                logger.error(f"Error closing connection pool: {e}")
                sentry_sdk.capture_exception(e)

    """
    executes SQLite queries
    returns cursor
    """

    def __execute_query(self, query, params=None):
        try:
            with sentry_sdk.start_span(op="db.query", description=query[:50]) as span:
                # Add query metadata
                span.set_tag("query_type", query.split()[0].upper())
                span.set_data("query", query)  # Will be sanitized by Sentry

                # Add timing information
                start_time = time.time()
                cursor = self.conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                self.conn.commit()
                duration = time.time() - start_time

                # Record query performance
                span.set_data("duration", duration)
                if duration > 1.0:  # Log slow queries
                    logger.warning(f"Slow query detected: {duration:.2f}s")
                    sentry_sdk.capture_message(
                        "Slow database query detected",
                        level="warning",
                        extras={
                            "query_duration": duration,
                            "query_type": query.split()[0].upper(),
                        },
                    )

                return cursor
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            sentry_sdk.capture_exception(e)
            raise

    """
    Creates a users table if it doesn't exist
    returns N/A
    """

    def create_users_table(self):
        try:
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
        except Exception as e:
            logger.error(f"Error creating users table: {e}")
            sentry_sdk.capture_exception(e)
            raise

    """
    Inserts a user
    Doesn't do any validation
    hashing is done inside the function
    returns N/A
    """

    def insert_user(self, username, password):
        try:
            with sentry_sdk.start_span(
                op="db.insert_user", description=f"Insert user {username}"
            ) as span:
                salt = os.urandom(16).hex()
                password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
                query = "INSERT INTO users (username, password_hash, salt) VALUES (%s, %s, %s)"
                self.__execute_query(query, (username, password_hash, salt))
        except Exception as e:
            logger.error(f"Error inserting user {username}: {e}")
            sentry_sdk.capture_exception(e)
            raise

    """
    Checks if a user is inside the database
    return N/A
    """

    def verify_user(self, username, password):
        try:
            with sentry_sdk.start_span(
                op="db.verify_user", description=f"Verify user {username}"
            ) as span:
                query = "SELECT password_hash, salt FROM users WHERE username = %s"
                cursor = self.__execute_query(query, (username,))
                result = cursor.fetchone()
                if result:
                    stored_hash, salt = result
                    password_hash = hashlib.sha256(
                        (password + salt).encode()
                    ).hexdigest()
                    return stored_hash == password_hash
                return False
        except Exception as e:
            logger.error(f"Error verifying user {username}: {e}")
            sentry_sdk.capture_exception(e)
            return False

    """
    Table for user login times
    Stores ID and login times
    returns N/A
    """

    def create_logins_table(self):
        try:
            c = self.conn.cursor()
            c.execute("""
            CREATE TABLE IF NOT EXISTS logins (
                id serial PRIMARY KEY,
                username TEXT,
                time numeric
            )""")
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error creating logins table: {e}")
            sentry_sdk.capture_exception(e)
            raise

    """
    Inserts login times for a givern username
    Time is rounded to 2 dp
    returns N/A
    """

    def insert_login_attempt(self, username, time):
        try:
            with sentry_sdk.start_span(
                op="db.insert_login", description=f"Insert login for {username}"
            ) as span:
                query = "INSERT INTO logins (username, time) VALUES(%s, %s)"
                self.__execute_query(query, (username, f"{time:.2f}"))
        except Exception as e:
            logger.error(f"Error inserting login attempt for {username}: {e}")
            sentry_sdk.capture_exception(e)
            raise

    """
    Retrive login attemps
    returns the attemps as an array if there are any
    returns N/A
    """

    def get_login_attemps(self, username):
        try:
            with sentry_sdk.start_span(
                op="db.get_logins", description=f"Get logins for {username}"
            ) as span:
                query = "SELECT username, time FROM logins WHERE username = %s"
                cursor = self.__execute_query(query, (username,))
                if cursor is not None:
                    return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting login attempts for {username}: {e}")
            sentry_sdk.capture_exception(e)
            return None

    """
    Creates a table to store games
    Store game positions as FEN
    returns N/A
    """

    def create_games_table(self):
        try:
            with sentry_sdk.start_span(
                op="db.create_games_table", description="Create games table"
            ) as span:
                c = self.conn.cursor()
                c.execute("""
                    CREATE TABLE IF NOT EXISTS games (
                        id SERIAL PRIMARY KEY,
                        player1 TEXT,
                        player2 TEXT,
                        fen TEXT
                    )
                """)
                self.conn.commit()
        except Exception as e:
            logger.error(f"Error creating games table: {e}")
            sentry_sdk.capture_exception(e)
            raise

    """
    Adds game to the games table
    returns N/A
    """

    def insert_game(self, player1, player2, fen):
        try:
            with sentry_sdk.start_span(
                op="db.insert_game",
                description=f"Insert game for players {player1} vs {player2}",
            ) as span:
                query = "INSERT INTO games (player1, player2, fen) VALUES (%s, %s, %s)"
                self.__execute_query(query, (player1, player2, fen))
        except Exception as e:
            logger.error(f"Error inserting game: {e}")
            sentry_sdk.capture_exception(e)
            raise

    def init_game_state(self, game_id, initial_state):
        try:
            with sentry_sdk.start_span(
                op="db.init_game", description=f"Initialize game {game_id}"
            ) as span:
                query = "INSERT INTO games (game_id, initial_state) VALUES (%s, %s)"
                self.__execute_query(query, (game_id, initial_state))
        except Exception as e:
            logger.error(f"Error initializing game state for game {game_id}: {e}")
            sentry_sdk.capture_exception(e)
            raise

    def update_game_state(self, game_id, final_state):
        try:
            with sentry_sdk.start_span(
                op="db.update_game", description=f"Update game {game_id}"
            ) as span:
                query = "UPDATE games SET final_state = %s WHERE game_id = %s"
                self.__execute_query(query, (final_state, game_id))
        except Exception as e:
            logger.error(f"Error updating game state for game {game_id}: {e}")
            sentry_sdk.capture_exception(e)
            raise

    def get_game_state(self, game_id):
        try:
            with sentry_sdk.start_span(
                op="db.get_game", description=f"Get game {game_id}"
            ) as span:
                query = (
                    "SELECT initial_state, final_state FROM games WHERE game_id = %s"
                )
                cursor = self.__execute_query(query, (game_id,))
                if cursor is not None:
                    return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error getting game state for game {game_id}: {e}")
            sentry_sdk.capture_exception(e)
            return None


if __name__ == "__main__":
    db = DBConnector()
    db.create_users_table()
    db.create_logins_table()
