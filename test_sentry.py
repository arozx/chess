import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from gui import ChessBoardUI
import sentry_sdk
import time


def run_test_sequence(window):
    """Run a sequence of test actions"""
    try:
        # Test 1: Login attempt with invalid credentials
        print("Testing invalid login...")
        window.username_input.setText("test_user")
        window.password_input.setText("wrong_password")
        window.handle_login()

        # Test 2: Invalid move attempt
        print("Testing invalid move...")
        window.handle_click(0, 0)  # Select a piece
        window.handle_click(5, 5)  # Try an invalid move

        # Test 3: AI move with performance monitoring
        print("Testing AI move...")
        window.ai_move()

        # Test 4: Simulate a slow operation
        print("Testing performance monitoring...")
        with sentry_sdk.start_span(
            op="test.slow_operation", description="Slow operation test"
        ):
            time.sleep(2)

        # Test 5: Generate an error
        print("Testing error handling...")
        raise ValueError("Test error for Sentry")

    except Exception as e:
        sentry_sdk.capture_exception(e)
        print(f"Test sequence completed with expected error: {e}")

    finally:
        # Exit after tests
        QTimer.singleShot(1000, lambda: sys.exit(0))


if __name__ == "__main__":
    print("Starting Sentry integration tests...")
    app = QApplication(sys.argv)
    window = ChessBoardUI()
    window.show()

    # Start test sequence after UI is shown
    QTimer.singleShot(500, lambda: run_test_sequence(window))

    sys.exit(app.exec_())
