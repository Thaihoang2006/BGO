import secrets
import string
import json
import html
import datetime
from typing import Optional, Dict, Any, Tuple, List
from backend.database import db
from backend.models.room import Room, RoomPlayer, MatchEvent
from backend.config import Config
from backend.games import get_game_engine

DEFAULT_PALETTE_COLORS = [
    "#FF9966", "#FFE1BA", "#BE807D", "#795463",
    "#4FD1C5", "#63B3ED", "#B794F4", "#F6AD55",
    "#68D391", "#FC8181", "#F6E05E", "#4299E1",
    "#ED64A6", "#38B2AC", "#9F7AEA", "#ED8936",
    "#48BB78", "#E53E3E", "#D69E2E", "#319795"
]

DEFAULT_SYMBOLS = [
    "X", "O", "▲", "■", "★", "♦", "●", "♠",
    "♣", "♥", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20"
]

_chat_last_sent: Dict[str, float] = {}

class RoomService:

    @staticmethod
    def generate_room_code(prefix: str = "BGO") -> str:
        """Generate unique room code like BGO742."""
        clean_chars = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
        for _ in range(50):
            suffix = "".join(secrets.choice(clean_chars) for _ in range(3))
            code = f"{prefix}{suffix}"
            row = db.fetch_one("SELECT id FROM rooms WHERE code = %s", (code,))
            if not row:
                return code
        return f"{prefix}{secrets.token_hex(2).upper()}"

    @staticmethod
    def _load_room_players(room: Room):
        if not room:
            return
        rows = db.fetch_all("SELECT * FROM room_players WHERE room_id = %s ORDER BY player_index ASC", (room.id,))
        room.players = [RoomPlayer.from_row(r) for r in rows]

    @staticmethod
    def get_room_by_code(room_code: str) -> Optional[Room]:
        code = room_code.strip().upper()
        row = db.fetch_one("SELECT * FROM rooms WHERE code = %s", (code,))
        if not row:
            return None
        room = Room.from_row(row)
        RoomService._load_room_players(room)
        return room

    @staticmethod
    def get_player_by_token(participant_token: str) -> Optional[RoomPlayer]:
        row = db.fetch_one("SELECT * FROM room_players WHERE participant_token = %s", (participant_token,))
        return RoomPlayer.from_row(row)

    @staticmethod
    def create_room(game_type: str, host_name: str, is_local: bool = False,
                    local_players: Optional[List[Dict[str, Any]]] = None,
                    settings: Optional[Dict[str, Any]] = None,
                    custom_max_players: Optional[int] = None) -> Tuple[Room, RoomPlayer, str]:
        game_meta = Config.GAMES.get(game_type)
        if not game_meta:
            raise ValueError(f"Không hỗ trợ game: {game_type}")

        room_code = RoomService.generate_room_code()
        host_token = secrets.token_hex(16)
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()

        status = "playing" if is_local else "waiting"
        max_players = int(custom_max_players) if custom_max_players else game_meta["max_players"]
        min_players = game_meta["min_players"]
        settings_dict = settings or {}
        settings_json = json.dumps(settings_dict, ensure_ascii=False)

        room_id = db.execute(
            """
            INSERT INTO rooms (code, game_type, status, max_players, min_players, is_local, host_token, state_version, settings_data, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (room_code, game_type, status, max_players, min_players, 1 if is_local else 0, host_token, 0, settings_json, now_str, now_str)
        )

        room = Room(
            id=room_id,
            code=room_code,
            game_type=game_type,
            status=status,
            max_players=max_players,
            min_players=min_players,
            is_local=is_local,
            host_token=host_token,
            state_version=0,
            settings_data=settings_json,
            created_at=now_str,
            updated_at=now_str
        )

        if is_local:
            players_data = local_players or [
                {"name": host_name or "Người chơi 1", "color": DEFAULT_PALETTE_COLORS[0]},
                {"name": "Người chơi 2", "color": DEFAULT_PALETTE_COLORS[1]}
            ]
            first_player = None
            players_objs = []
            for idx, p in enumerate(players_data):
                tok = secrets.token_hex(16)
                p_name = p.get("name", f"Người chơi {idx + 1}").strip() or f"Người chơi {idx + 1}"
                color = p.get("color", DEFAULT_PALETTE_COLORS[idx % len(DEFAULT_PALETTE_COLORS)])
                symbol = DEFAULT_SYMBOLS[idx % len(DEFAULT_SYMBOLS)]
                is_host = (idx == 0)

                rp_id = db.execute(
                    """
                    INSERT INTO room_players (room_id, participant_token, player_index, name, color, symbol, is_host, is_ready, is_connected, joined_at, last_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (room_id, tok, idx, p_name, color, symbol, 1 if is_host else 0, 1, 1, now_str, now_str)
                )
                rp = RoomPlayer(
                    id=rp_id,
                    room_id=room_id,
                    participant_token=tok,
                    player_index=idx,
                    name=p_name,
                    color=color,
                    symbol=symbol,
                    is_host=is_host,
                    is_ready=True,
                    is_connected=True,
                    joined_at=now_str,
                    last_active=now_str
                )
                players_objs.append(rp)
                if idx == 0:
                    first_player = rp

            room.players = players_objs

            # Initial game state
            engine = get_game_engine(game_type)
            engine_players = [
                {"player_index": p.player_index, "name": p.name, "color": p.color, "symbol": p.symbol}
                for p in room.players
            ]
            engine_players.sort(key=lambda x: x["player_index"])
            if game_type == "undercover":
                initial_state = engine.create_initial_state(engine_players, options=settings_dict)
            else:
                initial_state = engine.create_initial_state(engine_players)
            state_json = json.dumps(initial_state, ensure_ascii=False)

            db.execute(
                "UPDATE rooms SET game_state_data = %s, state_version = 1, updated_at = %s WHERE id = %s",
                (state_json, now_str, room_id)
            )
            room.game_state_data = state_json
            room.state_version = 1
            return room, first_player, host_token

        else:
            # Online room: host joins
            h_name = host_name.strip() or "Chủ phòng"
            color = DEFAULT_PALETTE_COLORS[0]
            symbol = DEFAULT_SYMBOLS[0]

            rp_id = db.execute(
                """
                INSERT INTO room_players (room_id, participant_token, player_index, name, color, symbol, is_host, is_ready, is_connected, joined_at, last_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (room_id, host_token, 0, h_name, color, symbol, 1, 1, 1, now_str, now_str)
            )
            host_player = RoomPlayer(
                id=rp_id,
                room_id=room_id,
                participant_token=host_token,
                player_index=0,
                name=h_name,
                color=color,
                symbol=symbol,
                is_host=True,
                is_ready=True,
                is_connected=True,
                joined_at=now_str,
                last_active=now_str
            )
            room.players = [host_player]
            return room, host_player, host_token

    @staticmethod
    def join_room(room_code: str, player_name: str, role: str = "player") -> Tuple[Room, RoomPlayer, str]:
        room = RoomService.get_room_by_code(room_code)
        if not room:
            raise ValueError(f"Không tìm thấy phòng với mã '{room_code}'")

        official_players = [p for p in room.players if not getattr(p, "is_spectator", False)]
        spectators = [p for p in room.players if getattr(p, "is_spectator", False)]

        is_spectator = (role == "spectator")
        if not is_spectator:
            if room.status != "waiting":
                raise ValueError("Phòng đã bắt đầu chơi hoặc đã kết thúc. Bạn có thể tham gia với vai trò Khán giả.")
            if len(official_players) >= room.max_players:
                raise ValueError("Phòng đã đủ số người chơi chính thức. Bạn có thể tham gia với vai trò Khán giả.")

        if is_spectator:
            max_spec = getattr(Config, "MAX_SPECTATORS_PER_ROOM", 30)
            if len(spectators) >= max_spec:
                raise ValueError(f"Phòng đã đủ số lượng khán giả tối đa ({max_spec} người)")
            next_index = 1000 + len(spectators)
            color = "#A0AEC0"
            symbol = "👁️"
            is_ready = True
        else:
            next_index = len(official_players)
            color = DEFAULT_PALETTE_COLORS[next_index % len(DEFAULT_PALETTE_COLORS)]
            symbol = DEFAULT_SYMBOLS[next_index % len(DEFAULT_SYMBOLS)]
            is_ready = False

        participant_token = secrets.token_hex(16)
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        name = player_name.strip() or (f"Khán giả {len(spectators) + 1}" if is_spectator else f"Người chơi {next_index + 1}")

        rp_id = db.execute(
            """
            INSERT INTO room_players (room_id, participant_token, player_index, name, color, symbol, is_host, is_ready, is_connected, is_spectator, joined_at, last_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (room.id, participant_token, next_index, name, color, symbol, 0, 1 if is_ready else 0, 1, 1 if is_spectator else 0, now_str, now_str)
        )

        new_player = RoomPlayer(
            id=rp_id,
            room_id=room.id,
            participant_token=participant_token,
            player_index=next_index,
            name=name,
            color=color,
            symbol=symbol,
            is_host=False,
            is_ready=is_ready,
            is_connected=True,
            is_spectator=is_spectator,
            joined_at=now_str,
            last_active=now_str
        )
        room.players.append(new_player)
        return room, new_player, participant_token

    @staticmethod
    def start_game(room_code: str, host_token: str) -> Room:
        room = RoomService.get_room_by_code(room_code)
        if not room:
            raise ValueError("Phòng không tồn tại")

        if room.host_token != host_token:
            raise ValueError("Chỉ chủ phòng mới có quyền bắt đầu ván chơi")

        if room.status != "waiting":
            raise ValueError(f"Không thể bắt đầu phòng ở trạng thái '{room.status}'")

        official_players = [p for p in room.players if not getattr(p, "is_spectator", False)]
        if len(official_players) < room.min_players:
            raise ValueError(f"Cần tối thiểu {room.min_players} người chơi để bắt đầu (hiện có {len(official_players)})")

        not_ready = [p.name for p in official_players if not p.is_host and not p.is_ready]
        if not_ready:
            raise ValueError(f"Người chơi chưa sẵn sàng: {', '.join(not_ready)}")

        engine = get_game_engine(room.game_type)
        engine_players = [
            {"player_index": p.player_index, "name": p.name, "color": p.color, "symbol": p.symbol}
            for p in official_players
        ]
        engine_players.sort(key=lambda x: x["player_index"])

        if room.game_type == "undercover":
            initial_state = engine.create_initial_state(engine_players, options=room.settings)
        else:
            initial_state = engine.create_initial_state(engine_players)
        state_json = json.dumps(initial_state, ensure_ascii=False)
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()

        db.execute(
            """
            UPDATE rooms
            SET status = 'playing', game_state_data = %s, state_version = 1, winner_data = NULL, updated_at = %s
            WHERE id = %s
            """,
            (state_json, now_str, room.id)
        )

        room.status = "playing"
        room.game_state_data = state_json
        room.state_version = 1
        room.winner_data = None
        room.updated_at = now_str
        return room

    @staticmethod
    def set_player_ready(room_code: str, participant_token: str, is_ready: bool) -> RoomPlayer:
        room = RoomService.get_room_by_code(room_code)
        if not room:
            raise ValueError("Phòng không tồn tại")

        player = next((p for p in room.players if p.participant_token == participant_token), None)
        if not player:
            raise ValueError("Người chơi không hợp lệ")

        if getattr(player, "is_spectator", False):
            return player

        db.execute(
            "UPDATE room_players SET is_ready = %s WHERE id = %s",
            (1 if is_ready else 0, player.id)
        )
        player.is_ready = is_ready
        return player

    @staticmethod
    def process_action(room_code: str, participant_token: str, action: Dict[str, Any], client_version: Optional[int] = None) -> Tuple[Room, Dict[str, Any]]:
        room = RoomService.get_room_by_code(room_code)
        if not room:
            raise ValueError("Phòng không tồn tại")

        if room.status != "playing":
            raise ValueError("Ván chơi chưa bắt đầu hoặc đã kết thúc")

        # Authorization check
        player = next((p for p in room.players if p.participant_token == participant_token), None)
        if not player:
            if room.is_local and room.host_token == participant_token:
                current_player_idx = room.game_state.get("current_player", 0)
                player = next((p for p in room.players if p.player_index == current_player_idx), None)
            if not player:
                raise ValueError("Xác thực người chơi thất bại")

        if getattr(player, "is_spectator", False):
            raise ValueError("Khán giả không thể thực hiện hành động trong trận đấu.")

        # Concurrency version check
        if client_version is not None and client_version != room.state_version:
            raise ValueError(f"Trạng thái bàn chơi đã thay đổi (client: {client_version}, server: {room.state_version}). Vui lòng tải lại bàn cờ.")

        engine = get_game_engine(room.game_type)
        current_state = room.game_state
        player_index = player.player_index

        # Validate action
        is_valid, error_msg = engine.validate_action(current_state, player_index, action)
        if not is_valid:
            raise ValueError(error_msg or "Nước đi không hợp lệ")

        # Apply action
        new_state, event_data = engine.apply_action(current_state, player_index, action)

        room.game_state = new_state
        room.state_version += 1
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        room.updated_at = now_str

        winner_json = None
        new_status = room.status
        scores_json = room.session_scores_data
        if new_state.get("status") == "finished" or new_state.get("phase") == "finished":
            new_status = "finished"
            room.status = "finished"
            room.winner = new_state.get("winner")
            winner_json = json.dumps(room.winner, ensure_ascii=False) if room.winner else None

            # Increment session match scores
            if room.winner and room.winner.get("player_index") is not None:
                win_idx = str(room.winner["player_index"])
                curr_scores = room.session_scores
                curr_scores[win_idx] = curr_scores.get(win_idx, 0) + 1
                room.session_scores = curr_scores
                scores_json = room.session_scores_data

        state_json = json.dumps(new_state, ensure_ascii=False)
        db.execute(
            """
            UPDATE rooms
            SET game_state_data = %s, state_version = %s, status = %s, winner_data = %s,
                session_scores_data = %s, updated_at = %s
            WHERE id = %s
            """,
            (state_json, room.state_version, new_status, winner_json, scores_json, now_str, room.id)
        )

        # Log match event
        payload_json = json.dumps(action, ensure_ascii=False)
        db.execute(
            """
            INSERT INTO match_events (room_id, sequence_number, player_index, action_type, payload_data, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (room.id, room.state_version, player_index, action.get("type", "unknown"), payload_json, now_str)
        )

        return room, event_data

    @staticmethod
    def _do_restart(room: Room) -> Room:
        engine = get_game_engine(room.game_type)
        official_players = [p for p in room.players if not getattr(p, "is_spectator", False)]
        engine_players = [
            {"player_index": p.player_index, "name": p.name, "color": p.color, "symbol": p.symbol}
            for p in official_players
        ]
        engine_players.sort(key=lambda x: x["player_index"])

        if room.game_type == "undercover":
            initial_state = engine.create_initial_state(engine_players, options=room.settings)
        else:
            initial_state = engine.create_initial_state(engine_players)
        state_json = json.dumps(initial_state, ensure_ascii=False)
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        new_version = room.state_version + 1

        db.execute(
            """
            UPDATE rooms
            SET status = 'playing', game_state_data = %s, state_version = %s, winner_data = NULL,
                rematch_votes_data = '[]', updated_at = %s
            WHERE id = %s
            """,
            (state_json, new_version, now_str, room.id)
        )

        room.status = "playing"
        room.game_state_data = state_json
        room.state_version = new_version
        room.winner_data = None
        room.rematch_votes = []
        room.updated_at = now_str
        return room

    @staticmethod
    def restart_game(room_code: str, participant_token: str) -> Room:
        room = RoomService.get_room_by_code(room_code)
        if not room:
            raise ValueError("Phòng không tồn tại")

        player = next((p for p in room.players if p.participant_token == participant_token), None)
        if not player or not player.is_host:
            raise ValueError("Chỉ chủ phòng mới có thể bắt đầu lại ván chơi")

        return RoomService._do_restart(room)

    @staticmethod
    def request_rematch(room_code: str, participant_token: str) -> Tuple[Room, bool, str]:
        room = RoomService.get_room_by_code(room_code)
        if not room:
            raise ValueError("Phòng không tồn tại")

        player = next((p for p in room.players if p.participant_token == participant_token), None)
        if not player:
            raise ValueError("Người chơi không thuộc phòng này")

        if getattr(player, "is_spectator", False):
            raise ValueError("Khán giả không tham gia biểu quyết tái đấu.")

        if room.is_local:
            restarted_room = RoomService._do_restart(room)
            return restarted_room, True, f"{player.name} đã bắt đầu lại ván cờ"

        votes = set(room.rematch_votes)
        votes.add(participant_token)
        room.rematch_votes = list(votes)

        # Check if all connected official players agreed
        official_connected = [p for p in room.players if p.is_connected and not getattr(p, "is_spectator", False)]
        connected_tokens = {p.participant_token for p in official_connected}
        min_required = max(2, min(len(official_connected), room.min_players)) if len(official_connected) >= 2 else 1
        all_agreed = (len(votes.intersection(connected_tokens)) >= len(connected_tokens)) and len(votes) >= min_required

        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if all_agreed:
            restarted_room = RoomService._do_restart(room)
            return restarted_room, True, "Cả hai bên đã đồng ý! Bắt đầu ván mới"
        else:
            db.execute("UPDATE rooms SET rematch_votes_data = %s, updated_at = %s WHERE id = %s",
                       (room.rematch_votes_data, now_str, room.id))
            return room, False, f"{player.name} đã gửi yêu cầu chơi lại. Đang chờ đối thủ đồng ý"

    @staticmethod
    def decline_rematch(room_code: str, participant_token: str) -> Tuple[Room, str]:
        room = RoomService.get_room_by_code(room_code)
        if not room:
            raise ValueError("Phòng không tồn tại")
        player = next((p for p in room.players if p.participant_token == participant_token), None)
        name = player.name if player else "Đối thủ"
        room.rematch_votes = []
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        db.execute("UPDATE rooms SET rematch_votes_data = '[]', updated_at = %s WHERE id = %s",
                   (now_str, room.id))
        return room, f"{name} đã từ chối yêu cầu chơi lại"

    @staticmethod
    def switch_game(room_code: str, participant_token: str, new_game_type: str) -> Room:
        room = RoomService.get_room_by_code(room_code)
        if not room:
            raise ValueError("Phòng không tồn tại")

        player = next((p for p in room.players if p.participant_token == participant_token), None)
        if not player or not player.is_host:
            raise ValueError("Chỉ chủ phòng mới có quyền đổi trò chơi")

        valid_games = {k: (v["min_players"], v["max_players"]) for k, v in Config.GAMES.items()}
        if new_game_type not in valid_games:
            raise ValueError(f"Trò chơi '{new_game_type}' không hợp lệ")

        min_p, max_p = valid_games[new_game_type]
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Reset non-host readiness
        db.execute("UPDATE room_players SET is_ready = 0 WHERE room_id = %s AND is_host = 0", (room.id,))
        for p in room.players:
            if not p.is_host and not getattr(p, "is_spectator", False):
                p.is_ready = False

        db.execute(
            """
            UPDATE rooms
            SET game_type = %s, status = 'waiting', game_state_data = NULL, winner_data = NULL,
                rematch_votes_data = '[]', min_players = %s, max_players = %s, updated_at = %s
            WHERE id = %s
            """,
            (new_game_type, min_p, max_p, now_str, room.id)
        )

        room.game_type = new_game_type
        room.status = "waiting"
        room.game_state_data = None
        room.winner_data = None
        room.rematch_votes = []
        room.min_players = min_p
        room.max_players = max_p
        room.updated_at = now_str
        return room

    @staticmethod
    def update_room_settings(room_code: str, host_token: str, new_settings: Dict[str, Any]) -> Room:
        room = RoomService.get_room_by_code(room_code)
        if not room:
            raise ValueError("Phòng không tồn tại")
        if room.host_token != host_token:
            raise ValueError("Chỉ chủ phòng mới có quyền thay đổi cài đặt phòng")

        curr = room.settings
        curr.update(new_settings)
        room.settings = curr
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()

        db.execute("UPDATE rooms SET settings_data = %s, updated_at = %s WHERE id = %s",
                   (room.settings_data, now_str, room.id))
        return room

    @staticmethod
    def return_to_lobby(room_code: str, participant_token: str) -> Room:
        room = RoomService.get_room_by_code(room_code)
        if not room:
            raise ValueError("Phòng không tồn tại")

        player = next((p for p in room.players if p.participant_token == participant_token), None)
        if not player:
            raise ValueError("Người chơi không hợp lệ")

        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Reset non-host readiness
        db.execute("UPDATE room_players SET is_ready = 0 WHERE room_id = %s AND is_host = 0", (room.id,))
        for p in room.players:
            if not p.is_host:
                p.is_ready = False

        db.execute(
            """
            UPDATE rooms
            SET status = 'waiting', game_state_data = NULL, winner_data = NULL,
                rematch_votes_data = '[]', updated_at = %s
            WHERE id = %s
            """,
            (now_str, room.id)
        )

        room.status = "waiting"
        room.game_state_data = None
        room.winner_data = None
        room.rematch_votes = []
        room.updated_at = now_str
        return room

    @staticmethod
    def update_connection_status(participant_token: str, is_connected: bool, socket_id: Optional[str] = None) -> Tuple[Optional[RoomPlayer], bool]:
        row = db.fetch_one("SELECT * FROM room_players WHERE participant_token = %s", (participant_token,))
        if not row:
            return None, False
        was_connected = bool(row.get("is_connected", 0))
        status_changed = (was_connected != bool(is_connected))

        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if socket_id is not None:
            db.execute(
                "UPDATE room_players SET is_connected = %s, socket_id = %s, last_active = %s WHERE id = %s",
                (1 if is_connected else 0, socket_id, now_str, row["id"])
            )
        else:
            db.execute(
                "UPDATE room_players SET is_connected = %s, last_active = %s WHERE id = %s",
                (1 if is_connected else 0, now_str, row["id"])
            )
        row["is_connected"] = is_connected
        row["last_active"] = now_str
        if socket_id:
            row["socket_id"] = socket_id
        return RoomPlayer.from_row(row), status_changed

    @staticmethod
    def leave_room(room_code: str, participant_token: str) -> Tuple[Optional[Room], Optional[str]]:
        room = RoomService.get_room_by_code(room_code)
        if not room:
            return None, "Phòng không tồn tại"

        player = next((p for p in room.players if p.participant_token == participant_token), None)
        if not player:
            return room, "Người chơi không tồn tại"

        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if room.status == "waiting":
            if player.is_host:
                db.execute("UPDATE rooms SET status = 'abandoned', updated_at = %s WHERE id = %s", (now_str, room.id))
                room.status = "abandoned"
                return room, "Chủ phòng đã rời đi, phòng đã đóng"
            else:
                db.execute("DELETE FROM room_players WHERE id = %s", (player.id,))
                room.players = [p for p in room.players if p.id != player.id]
                return room, f"Người chơi {player.name} đã rời phòng"
        else:
            if player.is_host:
                db.execute("UPDATE rooms SET status = 'abandoned', updated_at = %s WHERE id = %s", (now_str, room.id))
                room.status = "abandoned"
                return room, f"Chủ phòng {player.name} đã rời trận đấu, phòng chơi đã kết thúc"
            else:
                db.execute("UPDATE room_players SET is_connected = 0, last_active = %s WHERE id = %s", (now_str, player.id))
                player.is_connected = False
                return room, f"Người chơi {player.name} đã rời trận đấu"

    @staticmethod
    def transfer_host(room_code: str, current_host_token: str, new_host_player_index: int) -> Tuple[Room, RoomPlayer, RoomPlayer]:
        room = RoomService.get_room_by_code(room_code)
        if not room:
            raise ValueError("Phòng không tồn tại")

        current_host = next((p for p in room.players if p.participant_token == current_host_token and p.is_host), None)
        if not current_host:
            raise ValueError("Bạn không có quyền chuyển quyền chủ phòng")

        new_host = next((p for p in room.players if p.player_index == new_host_player_index and not getattr(p, "is_spectator", False)), None)
        if not new_host:
            raise ValueError("Người chơi được chọn không hợp lệ hoặc là khán giả")

        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        db.execute("UPDATE room_players SET is_host = 0, last_active = %s WHERE id = %s", (now_str, current_host.id))
        db.execute("UPDATE room_players SET is_host = 1, last_active = %s WHERE id = %s", (now_str, new_host.id))
        current_host.is_host = False
        new_host.is_host = True
        return room, current_host, new_host

    @staticmethod
    def add_chat_message(room_code: str, participant_token: Optional[str], message: str, msg_type: str = "user") -> Dict[str, Any]:
        room = RoomService.get_room_by_code(room_code)
        if not room:
            raise ValueError("Phòng không tồn tại")

        clean_msg = message.strip()
        if not clean_msg:
            raise ValueError("Nội dung tin nhắn không được để trống")
        if len(clean_msg) > 250:
            clean_msg = clean_msg[:250]

        safe_msg = html.escape(clean_msg)

        player_index = None
        sender_name = "Hệ thống"
        color = "#BE807D"
        is_host = False
        sender_role = "player"

        if participant_token:
            now_ts = datetime.datetime.now(datetime.timezone.utc).timestamp()
            last_ts = _chat_last_sent.get(participant_token, 0.0)
            if now_ts - last_ts < 0.4:
                raise ValueError("Bạn đang gửi tin nhắn quá nhanh. Vui lòng chờ giây lát.")
            _chat_last_sent[participant_token] = now_ts

            player = next((p for p in room.players if p.participant_token == participant_token), None)
            if player:
                player_index = player.player_index
                sender_name = player.name
                color = player.color
                is_host = player.is_host
                if getattr(player, "is_spectator", False):
                    sender_role = "spectator"
                    if room.settings.get("mute_spectator_chat", False):
                        raise ValueError("Chủ phòng đã tạm khóa chat đối với khán giả.")
            else:
                sender_name = "Khách"

        now_dt = datetime.datetime.now(datetime.timezone.utc)
        now_str = now_dt.isoformat()
        time_str = now_dt.strftime("%H:%M")

        msg_id = db.execute(
            """
            INSERT INTO room_messages (room_id, player_index, sender_name, color, message, msg_type, sender_role, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (room.id, player_index, sender_name, color, safe_msg, msg_type, sender_role, now_str)
        )

        return {
            "id": msg_id,
            "room_code": room.code,
            "player_index": player_index,
            "sender_name": sender_name,
            "color": color,
            "is_host": is_host,
            "message": safe_msg,
            "msg_type": msg_type,
            "sender_role": sender_role,
            "time": time_str,
            "created_at": now_str
        }

    @staticmethod
    def get_chat_messages(room_code: str, limit: int = 50) -> List[Dict[str, Any]]:
        room = RoomService.get_room_by_code(room_code)
        if not room:
            return []

        rows = db.fetch_all(
            """
            SELECT * FROM (
                SELECT * FROM room_messages WHERE room_id = %s ORDER BY id DESC LIMIT %s
            ) sub ORDER BY id ASC
            """,
            (room.id, limit)
        )

        messages = []
        for r in rows:
            created_at_val = str(r["created_at"])
            try:
                dt = datetime.datetime.fromisoformat(created_at_val.replace("Z", "+00:00"))
                time_str = dt.strftime("%H:%M")
            except Exception:
                time_str = ""

            messages.append({
                "id": r["id"],
                "room_code": room.code,
                "player_index": r["player_index"],
                "sender_name": r["sender_name"],
                "color": r["color"],
                "message": r["message"],
                "msg_type": r.get("msg_type", "user"),
                "sender_role": r.get("sender_role") or "player",
                "time": time_str,
                "created_at": created_at_val
            })
        return messages
