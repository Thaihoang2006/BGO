import pytest
from backend.services.room_service import RoomService
from backend.games.caro.engine import CaroEngine

def test_session_scores_and_mutual_rematch():
    # 1. Create online room for Caro
    room, p1, p1_token = RoomService.create_room("caro", "PlayerOne", is_local=False)
    room, p2, p2_token = RoomService.join_room(room.code, "PlayerTwo")
    RoomService.set_player_ready(room.code, p2_token, True)
    room = RoomService.start_game(room.code, p1_token)

    assert room.status == "playing"
    assert room.session_scores == {}

    # 2. Player 1 wins (5 in a row: row 7, cols 3..7)
    curr_v = 1
    for i in range(4):
        room, _ = RoomService.process_action(room.code, p1_token, {"type": "place_piece", "row": 7, "col": i + 3}, curr_v)
        curr_v += 1
        room, _ = RoomService.process_action(room.code, p2_token, {"type": "place_piece", "row": 8, "col": i + 3}, curr_v)
        curr_v += 1

    room, _ = RoomService.process_action(room.code, p1_token, {"type": "place_piece", "row": 7, "col": 7}, curr_v)
    assert room.status == "finished"
    assert room.winner["player_index"] == 0

    # Verify session score updated to 1 - 0!
    assert room.session_scores.get("0") == 1
    assert room.session_scores.get("1", 0) == 0

    # 3. Test mutual rematch agreement:
    # Player 1 requests rematch
    room, restarted, msg = RoomService.request_rematch(room.code, p1_token)
    assert restarted is False
    assert len(room.rematch_votes) == 1
    assert room.status == "finished"

    # Player 2 agrees to rematch
    room, restarted, msg = RoomService.request_rematch(room.code, p2_token)
    assert restarted is True
    assert room.status == "playing"
    assert len(room.rematch_votes) == 0
    # Score is preserved across games!
    assert room.session_scores.get("0") == 1

def test_switch_game():
    room, p1, p1_token = RoomService.create_room("caro", "HostAdmin", is_local=False)
    room, p2, p2_token = RoomService.join_room(room.code, "GuestUser")
    assert room.game_type == "caro"

    # Host switches to ludo
    room = RoomService.switch_game(room.code, p1_token, "ludo")
    assert room.game_type == "ludo"
    assert room.status == "waiting"
    assert room.max_players == 4

    # Non-host switches (should fail)
    with pytest.raises(ValueError, match="Chỉ chủ phòng"):
        RoomService.switch_game(room.code, p2_token, "monopoly")

def test_return_to_lobby():
    room, p1, p1_token = RoomService.create_room("caro", "HostPlayer", is_local=False)
    room, p2, p2_token = RoomService.join_room(room.code, "GuestPlayer")
    RoomService.set_player_ready(room.code, p2_token, True)
    room = RoomService.start_game(room.code, p1_token)
    assert room.status == "playing"

    # Return to lobby
    room = RoomService.return_to_lobby(room.code, p1_token)
    assert room.status == "waiting"
    assert room.game_state_data is None
    assert room.winner_data is None
    # Verify non-host readiness was reset so they can ready up again
    assert not any(p.is_ready for p in room.players if not p.is_host)
