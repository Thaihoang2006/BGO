from flask import request
from flask_socketio import emit, join_room, leave_room
from backend.extensions import socketio, db
from backend.services.room_service import RoomService
from backend.models.room import RoomPlayer, Room
from backend.games import get_game_engine

# Map socket ID to (room_code, participant_token)
sid_to_session = {}

def broadcast_game_state(room: Room, event_name: str, event_data: dict = None, extra: dict = None):
    extra = extra or {}
    engine = None
    try:
        engine = get_game_engine(room.game_type)
    except Exception:
        pass

    sids_in_room = [sid for sid, session in sid_to_session.items() if session[0] == room.code]

    for sid in sids_in_room:
        session = sid_to_session.get(sid)
        tok = session[1] if session else None
        viewer_idx = None
        if tok:
            p = next((x for x in room.players if x.participant_token == tok), None)
            if p and not getattr(p, "is_spectator", False):
                viewer_idx = p.player_index

        safe_state = room.game_state
        if engine and hasattr(engine, "get_public_state") and room.game_state:
            safe_state = engine.get_public_state(room.game_state, viewer_idx)

        payload = {
            "room_code": room.code,
            "game_type": room.game_type,
            "state_version": room.state_version,
            "game_state": safe_state,
            "status": room.status,
            "winner": room.winner,
            "room": room.to_dict(viewer_token=tok)
        }
        if event_data:
            payload["event"] = event_data
        payload.update(extra)
        emit(event_name, payload, room=sid)

def broadcast_room_dict(room: Room, event_name: str, payload_builder=None):
    sids_in_room = [sid for sid, session in sid_to_session.items() if session[0] == room.code]
    for sid in sids_in_room:
        session = sid_to_session.get(sid)
        tok = session[1] if session else None
        room_dict = room.to_dict(viewer_token=tok)
        payload = payload_builder(room_dict) if payload_builder else room_dict
        emit(event_name, payload, room=sid)

@socketio.on("connect")
def handle_connect():
    # Connection established
    pass

@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    session_info = sid_to_session.pop(sid, None)
    if session_info:
        room_code, token = session_info
        player, changed = RoomService.update_connection_status(token, is_connected=False)
        if player and changed:
            emit(
                "player_disconnected",
                {
                    "player_index": player.player_index,
                    "name": player.name,
                    "message": f"Người chơi {player.name} đã mất kết nối!"
                },
                to=room_code
            )

@socketio.on("join_room_socket")
def handle_join_room_socket(data):
    room_code = data.get("room_code", "").strip().upper()
    participant_token = data.get("participant_token")

    if not room_code:
        emit("error_msg", {"message": "Mã phòng không hợp lệ"})
        return

    room = RoomService.get_room_by_code(room_code)
    if not room:
        emit("error_msg", {"message": "Phòng không tồn tại"})
        return

    sid = request.sid
    join_room(room_code)
    sid_to_session[sid] = (room_code, participant_token)

    if participant_token:
        player, changed = RoomService.update_connection_status(participant_token, is_connected=True, socket_id=sid)
        # Only notify others if player had actually been disconnected (reconnecting)
        if player and changed:
            emit("player_connected", {
                "player_index": player.player_index,
                "name": player.name,
                "is_connected": True
            }, to=room_code)

    # Emit current state to this user
    emit("room_sync", room.to_dict(viewer_token=participant_token))

@socketio.on("set_ready")
def handle_set_ready(data):
    room_code = data.get("room_code", "").strip().upper()
    participant_token = data.get("participant_token")
    is_ready = bool(data.get("is_ready"))

    try:
        player = RoomService.set_player_ready(room_code, participant_token, is_ready)
        room = RoomService.get_room_by_code(room_code)
        broadcast_room_dict(room, "player_ready_changed", lambda rd: {
            "player_index": player.player_index,
            "is_ready": player.is_ready,
            "room": rd
        })
    except Exception as e:
        emit("error_msg", {"message": str(e)})

@socketio.on("start_game")
def handle_start_game(data):
    room_code = data.get("room_code", "").strip().upper()
    participant_token = data.get("participant_token")

    try:
        room = RoomService.start_game(room_code, participant_token)
        broadcast_game_state(room, "game_started")
    except Exception as e:
        emit("error_msg", {"message": str(e)})

@socketio.on("game_action")
def handle_game_action(data):
    room_code = data.get("room_code", "").strip().upper()
    participant_token = data.get("participant_token")
    action = data.get("action", {})
    client_version = data.get("client_version")

    try:
        room, event_data = RoomService.process_action(
            room_code=room_code,
            participant_token=participant_token,
            action=action,
            client_version=client_version
        )
        broadcast_game_state(room, "game_update", event_data=event_data)
    except Exception as e:
        emit("action_error", {"message": str(e)})

@socketio.on("update_settings")
def handle_update_settings(data):
    room_code = data.get("room_code", "").strip().upper()
    participant_token = data.get("participant_token")
    settings = data.get("settings", {})
    try:
        room = RoomService.update_room_settings(room_code, participant_token, settings)
        for sid, session in list(sid_to_session.items()):
            if session[0] == room.code:
                emit("room_sync", room.to_dict(viewer_token=session[1]), room=sid)
    except Exception as e:
        emit("error_msg", {"message": str(e)})

@socketio.on("restart_game")
def handle_restart_game(data):
    room_code = data.get("room_code", "").strip().upper()
    participant_token = data.get("participant_token")

    try:
        room = RoomService.restart_game(room_code, participant_token)
        broadcast_game_state(room, "game_restarted", extra={"session_scores": room.session_scores})
    except Exception as e:
        emit("error_msg", {"message": str(e)})

@socketio.on("request_rematch")
def handle_request_rematch(data):
    room_code = data.get("room_code", "").strip().upper()
    participant_token = data.get("participant_token")

    try:
        room, restarted, msg = RoomService.request_rematch(room_code, participant_token)
        if restarted:
            broadcast_game_state(room, "game_restarted", extra={"session_scores": room.session_scores})
        else:
            player = next((p for p in room.players if p.participant_token == participant_token), None)
            emit("rematch_requested", {
                "room_code": room.code,
                "requested_by": player.name if player else "Đối thủ",
                "player_index": player.player_index if player else None,
                "votes_count": len(room.rematch_votes),
                "total_needed": len([p for p in room.players if p.is_connected]),
                "message": msg
            }, to=room_code)
    except Exception as e:
        emit("error_msg", {"message": str(e)})

@socketio.on("decline_rematch")
def handle_decline_rematch(data):
    room_code = data.get("room_code", "").strip().upper()
    participant_token = data.get("participant_token")

    try:
        room, msg = RoomService.decline_rematch(room_code, participant_token)
        emit("rematch_declined", {
            "room_code": room.code,
            "message": msg
        }, to=room_code)
    except Exception as e:
        emit("error_msg", {"message": str(e)})

@socketio.on("switch_game")
def handle_switch_game(data):
    room_code = data.get("room_code", "").strip().upper()
    participant_token = data.get("participant_token")
    new_game_type = data.get("new_game_type")

    try:
        room = RoomService.switch_game(room_code, participant_token, new_game_type)
        broadcast_room_dict(room, "room_game_changed", lambda rd: {
            "room": rd,
            "new_game_type": new_game_type
        })
    except Exception as e:
        emit("error_msg", {"message": str(e)})

@socketio.on("return_to_lobby")
def handle_return_to_lobby(data):
    room_code = data.get("room_code", "").strip().upper()
    participant_token = data.get("participant_token")

    try:
        room = RoomService.return_to_lobby(room_code, participant_token)
        player = next((p for p in room.players if p.participant_token == participant_token), None)
        req_name = player.name if player else "Chủ phòng"
        broadcast_room_dict(room, "room_returned_to_lobby", lambda rd: {
            "room": rd,
            "requested_by": req_name
        })
    except Exception as e:
        emit("error_msg", {"message": str(e)})

@socketio.on("transfer_host")
def handle_transfer_host(data):
    room_code = data.get("room_code", "").strip().upper()
    participant_token = data.get("participant_token")
    new_host_index = data.get("new_host_player_index")
    try:
        room, old_host, new_host = RoomService.transfer_host(room_code, participant_token, int(new_host_index))
        broadcast_room_dict(room, "host_transferred", lambda rd: {
            "old_host_name": old_host.name,
            "new_host_name": new_host.name,
            "new_host_player_index": new_host.player_index,
            "room": rd
        })
        msg_obj = RoomService.add_chat_message(room_code, None, f"👑 {old_host.name} đã chuyển quyền Chủ phòng cho {new_host.name}!", msg_type="system")
        emit("new_chat_message", msg_obj, to=room_code)
    except Exception as e:
        emit("error_msg", {"message": str(e)})

@socketio.on("leave_room")
def handle_leave_room(data):
    room_code = data.get("room_code", "").strip().upper()
    participant_token = data.get("participant_token")

    pre_room = RoomService.get_room_by_code(room_code)
    player = next((p for p in pre_room.players if p.participant_token == participant_token), None) if pre_room else None

    room, msg = RoomService.leave_room(room_code, participant_token)
    leave_room(room_code)
    sid_to_session.pop(request.sid, None)

    if room and player:
        is_abandoned = (room.status == "abandoned")
        sids_in_room = [sid for sid, session in sid_to_session.items() if session[0] == room_code]
        for sid in sids_in_room:
            session = sid_to_session.get(sid)
            tok = session[1] if session else None
            emit("player_left", {
                "player_name": player.name,
                "player_index": player.player_index,
                "is_host": player.is_host,
                "room_closed": is_abandoned,
                "message": msg or f"Người chơi {player.name} đã rời phòng"
            }, room=sid)
            if not is_abandoned:
                emit("room_sync", room.to_dict(viewer_token=tok), room=sid)

    emit("left_room", {"message": msg or "Đã rời phòng"})

@socketio.on("send_chat")
@socketio.on("send_chat_message")
def handle_send_chat(data):
    room_code = data.get("room_code", "").strip().upper()
    participant_token = data.get("participant_token")
    message = data.get("message", "").strip()

    if not room_code or not message:
        return

    try:
        msg_obj = RoomService.add_chat_message(room_code, participant_token, message, msg_type="user")
        emit("new_chat_message", msg_obj, to=room_code)
    except Exception as e:
        emit("error_msg", {"message": f"Không thể gửi tin nhắn: {str(e)}"})
