import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "bgo_sunset_secret_key_default")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'bgo_dev.db'}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Supported Games Configuration
    GAMES = {
        "caro": {
            "id": "caro",
            "name": "Cờ Caro (Gomoku)",
            "subtitle": "Trận chiến 5 quân liên tiếp",
            "min_players": 2,
            "max_players": 2,
            "default_players": 2,
            "board_size": "15x15",
            "status": "ready",
            "badge": "Sẵn sàng"
        },
        "ludo": {
            "id": "ludo",
            "name": "Cờ Cá Ngựa (Ludo)",
            "subtitle": "Đua tài xúc xắc về đích",
            "min_players": 2,
            "max_players": 4,
            "default_players": 4,
            "board_size": "Bàn vuông 56 ô & 4 chuồng",
            "status": "ready",
            "badge": "Sẵn sàng"
        },
        "gem_kingdom": {
            "id": "gem_kingdom",
            "name": "Gem Kingdom (Splendor)",
            "subtitle": "Thu thập đá quý & mua thẻ phát triển",
            "min_players": 2,
            "max_players": 4,
            "default_players": 2,
            "board_size": "Bàn cờ 12 thẻ & Quý tộc",
            "status": "ready",
            "badge": "Sẵn sàng"
        },
        "monopoly": {
            "id": "monopoly",
            "name": "Cờ Tỷ Phú (Property Tycoon)",
            "subtitle": "Kinh doanh bất động sản & xây dựng cơ đồ",
            "min_players": 2,
            "max_players": 4,
            "default_players": 4,
            "board_size": "Bàn cờ tỷ phú 24 ô",
            "status": "ready",
            "badge": "Sẵn sàng"
        },
        "undercover": {
            "id": "undercover",
            "name": "Undercover (Ai Là Gián Điệp?)",
            "subtitle": "Truy tìm gián điệp & suy luận từ khóa bí mật",
            "min_players": 3,
            "max_players": 20,
            "default_players": 6,
            "board_size": "3 - 20 người chơi",
            "status": "ready",
            "badge": "Mới"
        }
    }

    MAX_SPECTATORS_PER_ROOM = 30

