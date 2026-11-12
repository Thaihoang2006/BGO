from flask_socketio import SocketIO
from backend.database import db

socketio = SocketIO(cors_allowed_origins="*", async_mode="threading")
