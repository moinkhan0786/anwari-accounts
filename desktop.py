import threading
import webview
import logging
import sys
import traceback
from app import app  # Import your Flask app

# ---------------------- Logging Setup ----------------------
log_format = '%(asctime)s - %(levelname)s - %(threadName)s - %(name)s - %(message)s'
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[
        logging.FileHandler('desktop_app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ---------------- Flask + Webview Threading ----------------
flask_ready = threading.Event()
flask_error = None

def run_flask():
    global flask_error
    try:
        logger.info("Starting Flask server on http://127.0.0.1:5000")
        flask_ready.set()
        app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False, threaded=True)
    except Exception as e:
        flask_error = e
        flask_ready.set()
        logger.exception("Flask server failed")

# ---------------- Desktop App Launcher ----------------
if __name__ == '__main__':
    logger.info("Launching Anwari Accounts Desktop App")

    # Start Flask thread
    flask_thread = threading.Thread(target=run_flask, name="FlaskThread", daemon=True)
    flask_thread.start()

    flask_ready.wait()
    if flask_error:
        logger.critical(f"Flask failed to start: {flask_error}")
        sys.exit(1)

    try:
        logger.info("Opening desktop window with Webview")
        webview.create_window(
            title="Anwari Accounts",
            url="http://127.0.0.1:5000",
            width=1280,
            height=800,
            resizable=True,
            confirm_close=True
        )
        webview.start()
        logger.info("Webview closed")

    except Exception as e:
        logger.exception("Webview failed")
        sys.exit(1)

    finally:
        if flask_thread.is_alive():
            logger.info("Flask thread still alive, exiting app")
        logging.shutdown()