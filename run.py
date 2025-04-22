import threading
import webview
from your_app_name.flask_app import app  # We'll create this next

def run_flask():
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    webview.create_window("Anwari Accounts", "http://127.0.0.1:5000", width=1200, height=800)
