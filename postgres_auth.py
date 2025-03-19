import os
import hashlib
import dotenv
from optional_dependencies import (
    SENTRY_AVAILABLE,
    PSYCOPG2_AVAILABLE,
    sentry_sdk,
    get_current_scope,
    psycopg2,
)
from logging_config import get_logger
import time

logger = get_logger(__name__)


class DBConnector:
    def __init__(self, env=True):
        if not PSYCOPG2_AVAILABLE:
            raise ImportError("psycopg2 is required for database operations")

        try:
            # Set database context for Sentry
            if SENTRY_AVAILABLE:
                scope = get_current_scope()
                if scope:
                    scope.set_tag("database.connection", "initializing")

            if env:
                dotenv.load_dotenv()
                # Use Neon's connection URL
                self.DATABASE_URL = os.getenv("DATABASE_URL")
            else:
                # For testing, don't include empty password in URL
                self.DATABASE_URL = "postgresql://postgres@localhost/userauth"

            # Update database context
            if SENTRY_AVAILABLE:
                scope = get_current_scope()
                if scope:
                    scope.set_tag(
                        "database.url", self.DATABASE_URL.split("@")[-1]
                    )  # Only log host/db, not credentials

            # Create connection pool without search_path option
            self.pool = psycopg2.pool.SimpleConnectionPool(1, 10, self.DATABASE_URL)
            if not self.pool:
                raise Exception("Failed to create connection pool")

            # Get initial connection and create schema if needed
            self.conn = self.pool.getconn()
            self.cursor = self.conn.cursor()

            # Create schema if it doesn't exist and set search path
            self.cursor.execute("CREATE SCHEMA IF NOT EXISTS public")
            self.cursor.execute("SET search_path TO public")
            self.conn.commit()

            # Set successful connection tag
            if SENTRY_AVAILABLE:
                scope = get_current_scope()
                if scope:
                    scope.set_tag("database.connection", "connected")

            # Set schema handling - only use schema prefix in non-test mode
            self._use_schema_prefix = env

        except Exception as e:
            if SENTRY_AVAILABLE:
                scope = get_current_scope()
                if scope:
                    scope.set_tag("database.connection", "failed")
                sentry_sdk.capture_exception(e)
            logger.error(f"Failed to initialize database connection: {e}")
            raise

    """
    Initiates connection to the database
    returns N/A
    """

    def _connect(self):
        try:
            if SENTRY_AVAILABLE:
                with sentry_sdk.start_span(
                    op="db.connect", description="Get connection from pool"
                ) as _:  # Use _ for unused span
                    if not self.conn or self.conn.closed:
                        self.conn = self.pool.getconn()
                        self.cursor = self.conn.cursor()
                        self.cursor.execute("SET search_path TO public")
                        self.conn.commit()
            else:
                if not self.conn or self.conn.closed:
                    self.conn = self.pool.getconn()
                    self.cursor = self.conn.cursor()
                    self.cursor.execute("SET search_path TO public")
                    self.conn.commit()
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            if SENTRY_AVAILABLE:
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
            if SENTRY_AVAILABLE:
                sentry_sdk.capture_exception(e)
        finally:
            try:
                if self.pool:
                    self.pool.closeall()
            except Exception as e:
                logger.error(f"Error closing connection pool: {e}")
                if SENTRY_AVAILABLE:
                    sentry_sdk.capture_exception(e)

    """
    executes SQLite queries
    returns cursor
    """

    def __execute_query(self, query, params=None):
        try:
            if SENTRY_AVAILABLE:
                with sentry_sdk.start_span(
                    op="db.query", description=query[:50]
                ) as _:  # Use _ for unused span
                    return self._execute_query_impl(query, params)
            else:
                return self._execute_query_impl(query, params)
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            if SENTRY_AVAILABLE:
                sentry_sdk.capture_exception(e)
            raise

    def _execute_query_impl(self, query, params, span=None):
        start_time = time.time()
        cursor = self.conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        self.conn.commit()
        duration = time.time() - start_time

        if span:
            span.set_tag("query_type", query.split()[0].upper())
            span.set_data("query", query)
            span.set_data("duration", duration)

        if duration > 1.0:
            logger.warning(f"Slow query detected: {duration:.2f}s")
            if SENTRY_AVAILABLE:
                sentry_sdk.capture_message(
                    "Slow database query detected",
                    level="warning",
                    extras={
                        "query_duration": duration,
                        "query_type": query.split()[0].upper(),
                    },
                )

        return cursor

    def _get_table_name(self, base_name: str) -> str:
        """Helper to get full table name with conditional schema prefix"""
        return f"public.{base_name}" if self._use_schema_prefix else base_name

    """
    Creates a users table if it doesn't exist
    returns N/A
    """

    def create_users_table(self):
        try:
            c = self.conn.cursor()
            table_name = self._get_table_name("users")
            c.execute(
                f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id serial PRIMARY KEY,
                username TEXT,
                password_hash TEXT,
                salt TEXT,
                UNIQUE(salt, username)
            )"""
            )
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error creating users table: {e}")
            if SENTRY_AVAILABLE:
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
            if SENTRY_AVAILABLE:
                with sentry_sdk.start_span(
                    op="db.insert_user", description=f"Insert user {username}"
                ) as _:  # Use _ for unused span
                    salt = os.urandom(16).hex()
                    password_hash = hashlib.sha256(
                        (password + salt).encode()
                    ).hexdigest()
                    query = f"INSERT INTO {self._get_table_name('users')} (username, password_hash, salt) VALUES (%s, %s, %s)"
                    self.__execute_query(query, (username, password_hash, salt))
            else:
                salt = os.urandom(16).hex()
                password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
                query = f"INSERT INTO {self._get_table_name('users')} (username, password_hash, salt) VALUES (%s, %s, %s)"
                self.__execute_query(query, (username, password_hash, salt))
        except Exception as e:
            logger.error(f"Error inserting user {username}: {e}")
            if SENTRY_AVAILABLE:
                sentry_sdk.capture_exception(e)
            raise

    """
    Checks if a user is inside the database
    return N/A
    """

    def verify_user(self, username, password):
        try:
            if SENTRY_AVAILABLE:
                with sentry_sdk.start_span(
                    op="db.verify_user", description=f"Verify user {username}"
                ) as _:  # Use _ for unused span
                    query = f"SELECT password_hash, salt FROM {self._get_table_name('users')} WHERE username = %s"
                    cursor = self.__execute_query(query, (username,))
                    result = cursor.fetchone()
                    if result:
                        stored_hash, salt = result
                        password_hash = hashlib.sha256(
                            (password + salt).encode()
                        ).hexdigest()
                        return stored_hash == password_hash
                    return False
            else:
                query = f"SELECT password_hash, salt FROM {self._get_table_name('users')} WHERE username = %s"
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
            if SENTRY_AVAILABLE:
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
            table_name = self._get_table_name("logins")
            c.execute(
                f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id serial PRIMARY KEY,
                username TEXT,
                time numeric
            )"""
            )
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error creating logins table: {e}")
            if SENTRY_AVAILABLE:
                sentry_sdk.capture_exception(e)
            raise

    """
    Inserts login times for a givern username
    Time is rounded to 2 dp
    returns N/A
    """

    def insert_login_attempt(self, username, time):
        try:
            if SENTRY_AVAILABLE:
                with sentry_sdk.start_span(
                    op="db.insert_login", description=f"Insert login for {username}"
                ) as _:  # Use _ for unused span
                    query = f"INSERT INTO {self._get_table_name('logins')} (username, time) VALUES(%s, %s)"
                    self.__execute_query(query, (username, f"{time:.2f}"))
            else:
                query = f"INSERT INTO {self._get_table_name('logins')} (username, time) VALUES(%s, %s)"
                self.__execute_query(query, (username, f"{time:.2f}"))
        except Exception as e:
            logger.error(f"Error inserting login attempt for {username}: {e}")
            if SENTRY_AVAILABLE:
                sentry_sdk.capture_exception(e)
            raise

    """
    Retrive login attemps
    returns the attemps as an array if there are any
    returns N/A
    """

    def get_login_attemps(self, username):
        try:
            if SENTRY_AVAILABLE:
                with sentry_sdk.start_span(
                    op="db.get_logins", description=f"Get logins for {username}"
                ) as _:  # Use _ for unused span
                    query = f"SELECT username, time FROM {self._get_table_name('logins')} WHERE username = %s"
                    cursor = self.__execute_query(query, (username,))
                    result = cursor.fetchall()  # Changed from cursor.fetchone()
                    return result if result else []  # Return empty list instead of None
            else:
                query = f"SELECT username, time FROM {self._get_table_name('logins')} WHERE username = %s"
                cursor = self.__execute_query(query, (username,))
                result = cursor.fetchall()
                return result if result else []
        except Exception as e:
            logger.error(f"Error getting login attempts for {username}: {e}")
            if SENTRY_AVAILABLE:
                sentry_sdk.capture_exception(e)
            return []  # Return empty list on error

    """
    Creates a table to store games
    Store game positions as FEN
    returns N/A
    """

    def create_games_table(self):
        try:
            if SENTRY_AVAILABLE:
                with sentry_sdk.start_span(
                    op="db.create_games_table", description="Create games table"
                ) as _:  # Use _ for unused span
                    c = self.conn.cursor()
                    c.execute(
                        """
                        CREATE TABLE IF NOT EXISTS public.games (
                            id SERIAL PRIMARY KEY,
                            player1 TEXT,
                            player2 TEXT,
                            fen TEXT
                        )
                    """
                    )
                    self.conn.commit()
            else:
                c = self.conn.cursor()
                c.execute(
                    """
                    CREATE TABLE IF NOT EXISTS public.games (
                        id SERIAL PRIMARY KEY,
                        player1 TEXT,
                        player2 TEXT,
                        fen TEXT
                    )
                """
                )
                self.conn.commit()
        except Exception as e:
            logger.error(f"Error creating games table: {e}")
            if SENTRY_AVAILABLE:
                sentry_sdk.capture_exception(e)
            raise

    """
    Adds game to the games table
    returns N/A
    """

    def insert_game(self, player1, player2, fen):
        try:
            if SENTRY_AVAILABLE:
                with sentry_sdk.start_span(
                    op="db.insert_game",
                    description=f"Insert game for players {player1} vs {player2}",
                ) as _:  # Use _ for unused span
                    query = (
                        "INSERT INTO games (player1, player2, fen) VALUES (%s, %s, %s)"
                    )
                    self.__execute_query(query, (player1, player2, fen))
            else:
                query = "INSERT INTO games (player1, player2, fen) VALUES (%s, %s, %s)"
                self.__execute_query(query, (player1, player2, fen))
        except Exception as e:
            logger.error(f"Error inserting game: {e}")
            if SENTRY_AVAILABLE:
                sentry_sdk.capture_exception(e)
            raise

    def init_game_state(self, game_id, initial_state):
        try:
            if SENTRY_AVAILABLE:
                with sentry_sdk.start_span(
                    op="db.init_game", description=f"Initialize game {game_id}"
                ) as _:  # Use _ for unused span
                    query = "INSERT INTO games (game_id, initial_state) VALUES (%s, %s)"
                    self.__execute_query(query, (game_id, initial_state))
            else:
                query = "INSERT INTO games (game_id, initial_state) VALUES (%s, %s)"
                self.__execute_query(query, (game_id, initial_state))
        except Exception as e:
            logger.error(f"Error initializing game state for game {game_id}: {e}")
            if SENTRY_AVAILABLE:
                sentry_sdk.capture_exception(e)
            raise

    def update_game_state(self, game_id, final_state):
        try:
            if SENTRY_AVAILABLE:
                with sentry_sdk.start_span(
                    op="db.update_game", description=f"Update game {game_id}"
                ) as _:  # Use _ for unused span
                    query = "UPDATE games SET final_state = %s WHERE game_id = %s"
                    self.__execute_query(query, (final_state, game_id))
            else:
                query = "UPDATE games SET final_state = %s WHERE game_id = %s"
                self.__execute_query(query, (final_state, game_id))
        except Exception as e:
            logger.error(f"Error updating game state for game {game_id}: {e}")
            if SENTRY_AVAILABLE:
                sentry_sdk.capture_exception(e)
            raise

    def get_game_state(self, game_id):
        try:
            if SENTRY_AVAILABLE:
                with sentry_sdk.start_span(
                    op="db.get_game", description=f"Get game {game_id}"
                ) as _:  # Use _ for unused span
                    query = "SELECT initial_state, final_state FROM games WHERE game_id = %s"
                    cursor = self.__execute_query(query, (game_id,))
                    if cursor is not None:
                        return cursor.fetchone()
            else:
                query = (
                    "SELECT initial_state, final_state FROM games WHERE game_id = %s"
                )
                cursor = self.__execute_query(query, (game_id,))
                if cursor is not None:
                    return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error getting game state for game {game_id}: {e}")
            if SENTRY_AVAILABLE:
                sentry_sdk.capture_exception(e)
            return None


if __name__ == "__main__":
    db = DBConnector()
    db.create_users_table()
    db.create_logins_table()
