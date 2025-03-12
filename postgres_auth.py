import psycopg2
import hashlib
import dotenv
import os
import sentry_sdk
from logging import getLogger
import time

logger = getLogger(__name__)


class DBConnector:
    def __init__(self, env=True):
        try:
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
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            sentry_sdk.capture_exception(e)
            raise

    """
    Initiates connection to the database
    returns N/A
    """

    def _connect(self):
        try:
            self.conn = psycopg2.connect(
                dbname=self.DB_NAME,
                user=self.DB_USER,
                host=self.DB_HOST,
                password=self.DB_PASSWORD,
            )

            self.cursor = self.conn.cursor()
            self.conn.commit()
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
            if self.conn:
                self.conn.close()
        except Exception as e:
            logger.error(f"Error disconnecting from database: {e}")
            sentry_sdk.capture_exception(e)

    """
    executes SQLite queries
    returns cursor
    """

    def __execute_query(self, query):
        try:
            with sentry_sdk.start_span(op="db", description=query[:50]) as span:
                span.set_tag("query_type", query.split()[0].upper())
                cursor = self.conn.cursor()
                cursor.execute(query)
                self.conn.commit()
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
                query = f"INSERT INTO users (username, password_hash, salt) VALUES ('{username}', '{password_hash}', '{salt}')"
                self.__execute_query(query)
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
                query = f"SELECT password_hash, salt FROM users WHERE username = '{username}'"
                cursor = self.__execute_query(query)
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
                query = f"INSERT INTO logins (username, time) VALUES('{username}', '{time:.2f}')"
                self.__execute_query(query)
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
                query = (
                    f"SELECT username, time FROM logins WHERE username = '{username}'"
                )
                cursor = self.__execute_query(query)
                if cursor is not None:
                    return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting login attempts for {username}: {e}")
            sentry_sdk.capture_exception(e)
            return None

    def test_sentry_functionality(self):
        """
        Test function to verify Sentry error reporting
        """
        try:
            # Test 1: Division by zero error
            logger.info("Testing Sentry with division by zero error")
            result = 1 / 0

        except Exception as e:
            logger.error(f"Caught test exception: {e}")
            sentry_sdk.capture_exception(e)

        try:
            # Test 2: Database connection error
            logger.info("Testing Sentry with invalid database connection")
            bad_connector = DBConnector()
            bad_connector.DB_HOST = "nonexistent-host"
            bad_connector._connect()

        except Exception as e:
            logger.error(f"Caught database test exception: {e}")
            sentry_sdk.capture_exception(e)

        # Test 3: Custom message
        logger.info("Testing Sentry with custom message")
        sentry_sdk.capture_message("Test message from chess application")

        # Test 4: Performance monitoring
        with sentry_sdk.start_span(
            op="test.performance", description="Test performance monitoring"
        ):
            logger.info("Testing performance monitoring")
            time.sleep(1)  # Simulate some work


if __name__ == "__main__":
    db = DBConnector()
    db.create_users_table()
    db.create_logins_table()

    # Run Sentry tests
    db.test_sentry_functionality()

    # create a user
    paswd = "jack2"
    user = "jack2"
    db.insert_user(user, paswd)
    logger.info(db.verify_user(user, paswd))
