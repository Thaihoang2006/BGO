import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.app import create_app
from backend.extensions import socketio

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5500))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"=================================================")
    print(f"   BGO - Board Games Online is launching...")
    print(f"   Local URL:    http://localhost:{port}")
    print(f"   Network URL:  http://127.0.0.1:{port}")
    print(f"=================================================")
    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)
