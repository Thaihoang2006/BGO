import json
import datetime
from typing import Optional, List, Dict, Any
from backend.database import db

class RoomPlayer:
    def __init__(self, id=None, room_id=None, participant_token=None, player_index=0,
                 name="", color="#FF9966", symbol="X", is_host=False, is_ready=False,
                 is_connected=True, is_spectator=False, socket_id=None, joined_at=None, last_active=None):
        self.id = id
        self.room_id = room_id
        self.participant_token = participant_token
        self.player_index = player_index
        self.name = name
        self.color = color
        self.symbol = symbol
        self.is_host = bool(is_host)
        self.is_ready = bool(is_ready)
        self.is_connected = bool(is_connected)
        self.is_spectator = bool(is_spectator)
        self.socket_id = socket_id
        self.joined_at = joined_at or datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.last_active = last_active or datetime.datetime.now(datetime.timezone.utc).isoformat()

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        is_spec = False
        try:
            is_spec = bool(row["is_spectator"])
        except (KeyError, IndexError):
            is_spec = False
        return cls(
            id=row["id"],
            room_id=row["room_id"],
            participant_token=row["participant_token"],
            player_index=row["player_index"],
            name=row["name"],
            color=row["color"],
            symbol=row["symbol"],
            is_host=bool(row["is_host"]),
            is_ready=bool(row["is_ready"]),
            is_connected=bool(row["is_connected"]),
            is_spectator=is_spec,
            socket_id=row["socket_id"],
            joined_at=str(row["joined_at"]),
            last_active=str(row["last_active"])
        )

    def to_dict(self, is_viewer=False):
        data = {
            "player_index": self.player_index,
            "name": self.name,
            "color": self.color,
            "symbol": self.symbol,
            "is_host": self.is_host,
            "is_ready": self.is_ready,
            "is_connected": self.is_connected,
            "is_spectator": self.is_spectator,
            "is_you": is_viewer
        }
        if is_viewer:
            data["participant_token"] = self.participant_token
        return data


class Room:
    def __init__(self, id=None, code="", game_type="caro", status="waiting",
                 max_players=2, min_players=2, is_local=False, host_token=None,
                 state_version=0, game_state_data=None, winner_data=None,
                 session_scores_data=None, rematch_votes_data=None, settings_data=None,
                 created_at=None, updated_at=None):
        self.id = id
        self.code = code
        self.game_type = game_type
        self.status = status
        self.max_players = max_players
        self.min_players = min_players
        self.is_local = bool(is_local)
        self.host_token = host_token
        self.state_version = state_version
        self.game_state_data = game_state_data
        self.winner_data = winner_data
        self.session_scores_data = session_scores_data or "{}"
        self.rematch_votes_data = rematch_votes_data or "[]"
        self.settings_data = settings_data or "{}"
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.updated_at = updated_at or datetime.datetime.now(datetime.timezone.utc).isoformat()
        self._players: List[RoomPlayer] = []

    @property
    def settings(self) -> Dict[str, Any]:
        if not self.settings_data:
            return {}
        try:
            return json.loads(self.settings_data)
        except Exception:
            return {}

    @settings.setter
    def settings(self, val: Dict[str, Any]):
        self.settings_data = json.dumps(val, ensure_ascii=False) if val is not None else "{}"

    @property
    def players(self) -> List[RoomPlayer]:
        return self._players

    @players.setter
    def players(self, val: List[RoomPlayer]):
        self._players = val

    @property
    def session_scores(self) -> Dict[str, int]:
        if not self.session_scores_data:
            return {}
        try:
            return json.loads(self.session_scores_data)
        except Exception:
            return {}

    @session_scores.setter
    def session_scores(self, val: Dict[str, int]):
        self.session_scores_data = json.dumps(val, ensure_ascii=False) if val is not None else "{}"

    @property
    def rematch_votes(self) -> List[str]:
        if not self.rematch_votes_data:
            return []
        try:
            return json.loads(self.rematch_votes_data)
        except Exception:
            return []

    @rematch_votes.setter
    def rematch_votes(self, val: List[str]):
        self.rematch_votes_data = json.dumps(val, ensure_ascii=False) if val is not None else "[]"

    @property
    def game_state(self):
        if not self.game_state_data:
            return None
        try:
            return json.loads(self.game_state_data)
        except Exception:
            return None

    @game_state.setter
    def game_state(self, value):
        self.game_state_data = json.dumps(value, ensure_ascii=False) if value is not None else None

    @property
    def winner(self):
        if not self.winner_data:
            return None
        try:
            return json.loads(self.winner_data)
        except Exception:
            return None

    @winner.setter
    def winner(self, value):
        self.winner_data = json.dumps(value, ensure_ascii=False) if value is not None else None

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row["id"],
            code=row["code"],
            game_type=row["game_type"],
            status=row["status"],
            max_players=row["max_players"],
            min_players=row["min_players"],
            is_local=bool(row["is_local"]),
            host_token=row["host_token"],
            state_version=row["state_version"],
            game_state_data=row["game_state_data"],
            winner_data=row["winner_data"],
            session_scores_data=row.get("session_scores_data") or "{}",
            rematch_votes_data=row.get("rematch_votes_data") or "[]",
            settings_data=row.get("settings_data") or "{}",
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"])
        )

    def to_dict(self, viewer_token=None):
        all_players = [p.to_dict(is_viewer=(p.participant_token == viewer_token)) for p in self.players]
        all_players.sort(key=lambda p: p["player_index"])

        players_list = [p for p in all_players if not p.get("is_spectator")]
        spectators_list = [p for p in all_players if p.get("is_spectator")]

        is_viewer_host = False
        is_viewer_spectator = False
        viewer_player_index = None
        has_voted_rematch = False
        rematch_voters = self.rematch_votes
        if viewer_token:
            for p in self.players:
                if p.participant_token == viewer_token:
                    is_viewer_host = p.is_host
                    is_viewer_spectator = getattr(p, "is_spectator", False)
                    viewer_player_index = None if is_viewer_spectator else p.player_index
                    has_voted_rematch = (viewer_token in rematch_voters)
                    break

        safe_state = self.game_state
        if self.game_state:
            try:
                from backend.games import get_game_engine
                engine = get_game_engine(self.game_type)
                if hasattr(engine, "get_public_state"):
                    safe_state = engine.get_public_state(self.game_state, viewer_player_index)
            except Exception:
                pass

        return {
            "room_code": self.code,
            "game_type": self.game_type,
            "status": self.status,
            "max_players": self.max_players,
            "min_players": self.min_players,
            "is_local": self.is_local,
            "state_version": self.state_version,
            "players": players_list,
            "player_count": len(players_list),
            "spectators": spectators_list,
            "spectator_count": len(spectators_list),
            "is_viewer_host": is_viewer_host,
            "is_viewer_spectator": is_viewer_spectator,
            "viewer_player_index": viewer_player_index,
            "has_voted_rematch": has_voted_rematch,
            "rematch_votes_count": len(rematch_voters),
            "session_scores": self.session_scores,
            "settings": self.settings,
            "game_state": safe_state,
            "winner": self.winner,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class MatchEvent:
    def __init__(self, id=None, room_id=None, sequence_number=0,
                 player_index=0, action_type="unknown", payload_data=None, created_at=None):
        self.id = id
        self.room_id = room_id
        self.sequence_number = sequence_number
        self.player_index = player_index
        self.action_type = action_type
        self.payload_data = payload_data
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    @property
    def payload(self):
        if not self.payload_data:
            return {}
        try:
            return json.loads(self.payload_data)
        except Exception:
            return {}

    @payload.setter
    def payload(self, value):
        self.payload_data = json.dumps(value, ensure_ascii=False) if value is not None else None
