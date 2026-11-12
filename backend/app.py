import os
import sys
from pathlib import Path

# Đảm bảo đường dẫn gốc dự án luôn nằm trong sys.path (đặc biệt khi bấm nút Run trực tiếp file app.py trong VS Code)
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from flask import Flask, send_from_directory, render_template, request
from flask_cors import CORS
from backend.config import Config
from backend.extensions import db, socketio
from backend.api.routes import api_bp
import backend.sockets.events # Register socket events

def create_app(config_class=Config):
    base_dir = Path(__file__).resolve().parent.parent
    frontend_dir = base_dir / "frontend"

    app = Flask(
        __name__,
        static_folder=str(frontend_dir / "static"),
        static_url_path="/static"
    )
    app.config.from_object(config_class)
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

    @app.after_request
    def add_header(response):
        if "static" in response.headers.get("Content-Disposition", "") or request.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

    CORS(app, resources={r"/*": {"origins": "*"}})
    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

    app.register_blueprint(api_bp)

    @app.route("/")
    def index():
        return send_from_directory(str(frontend_dir), "index.html")

    @app.route("/favicon.ico")
    def favicon():
        return send_from_directory(str(frontend_dir / "static" / "assets"), "favicon.ico", mimetype="image/vnd.microsoft.icon")

    # SPA catch-all fallback for client-side routing
    @app.route("/<path:path>")
    def catch_all(path):
        if path.startswith("api/") or path.startswith("static/"):
            return {"error": "Not found"}, 404
        return send_from_directory(str(frontend_dir), "index.html")

    with app.app_context():
        db.create_all()

    return app

if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5500))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"=================================================")
    print(f"   BGO - Board Games Online is launching...")
    print(f"   Local URL:    http://localhost:{port}")
    print(f"   Network URL:  http://127.0.0.1:{port}")
    print(f"=================================================")
    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)
