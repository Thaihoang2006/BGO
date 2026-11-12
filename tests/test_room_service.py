import os
import pytest
from backend.database import db
from backend.services.room_service import RoomService

@pytest.fixture(autouse=True)
def setup_test_db():
    # Use isolated test sqlite database
    test_db = "bgo_test.db"
    db.db_url = f"sqlite:///{test_db}"
    db.is_mysql = False
    db.create_tables()

    # Clear tables before each test
    db.execute("DELETE FROM match_events")
    db.execute("DELETE FROM room_players")
    db.execute("DELETE FROM rooms")
    yield
    # Cleanup
    db.execute("DELETE FROM match_events")
    db.execute("DELETE FROM room_players")
    db.execute("DELETE FROM rooms")

def test_create_online_room():
    room, host, token = RoomService.create_room("caro", "PlayerOne", is_local=False)
    assert room.code.startswith("BGO")
    assert room.status == "waiting"
    assert room.max_players == 2
    assert room.min_players == 2
    assert host.player_index == 0
    assert host.is_host is True
    assert host.name == "PlayerOne"
    assert token == host.participant_token

def test_join_online_room():
    room, host, token1 = RoomService.create_room("caro", "HostPlayer", is_local=False)
    room, player2, token2 = RoomService.join_room(room.code, "SecondPlayer")
    
    assert len(room.players) == 2
    assert player2.player_index == 1
    assert player2.is_host is False
    assert player2.is_ready is False
    assert token1 != token2

    # Try to join when room is full (max 2 players for Caro)
    with pytest.raises(ValueError, match="đủ số người chơi"):
        RoomService.join_room(room.code, "ThirdPlayer")

def test_start_game_validation():
    room, host, token1 = RoomService.create_room("caro", "HostPlayer", is_local=False)
    
    # Cannot start with only 1 player
    with pytest.raises(ValueError, match="tối thiểu 2 người"):
        RoomService.start_game(room.code, token1)

    room, p2, token2 = RoomService.join_room(room.code, "Player2")

    # Cannot start if Player 2 is not ready
    with pytest.raises(ValueError, match="chưa sẵn sàng"):
        RoomService.start_game(room.code, token1)

    # Player 2 readies up
    RoomService.set_player_ready(room.code, token2, True)

    # Non-host cannot start game
    with pytest.raises(ValueError, match="Chỉ chủ phòng"):
        RoomService.start_game(room.code, token2)

    # Host starts game successfully
    started_room = RoomService.start_game(room.code, token1)
    assert started_room.status == "playing"
    assert started_room.game_state is not None
    assert started_room.game_state["current_player"] == 0
    assert started_room.state_version == 1

def test_game_actions_and_turns():
    room, host, token1 = RoomService.create_room("caro", "P1", is_local=False)
    room, p2, token2 = RoomService.join_room(room.code, "P2")
    RoomService.set_player_ready(room.code, token2, True)
    RoomService.start_game(room.code, token1)

    # Player 2 tries to play first -> error
    with pytest.raises(ValueError, match="lượt"):
        RoomService.process_action(room.code, token2, {"type": "place_piece", "row": 7, "col": 7})

    # Player 1 plays (7, 7) -> OK
    room, event = RoomService.process_action(
        room.code, token1, {"type": "place_piece", "row": 7, "col": 7}, client_version=1
    )
    assert room.state_version == 2
    assert room.game_state["grid"][7][7] == "X"
    assert room.game_state["current_player"] == 1

    # Player 2 plays (7, 8) -> OK
    room, event = RoomService.process_action(
        room.code, token2, {"type": "place_piece", "row": 7, "col": 8}, client_version=2
    )
    assert room.state_version == 3
    assert room.game_state["grid"][7][8] == "O"
    assert room.game_state["current_player"] == 0

def test_local_multiplayer_room():
    local_players = [
        {"name": "An", "color": "#FF9966"},
        {"name": "Bình", "color": "#FFE1BA"}
    ]
    room, host, token = RoomService.create_room("caro", "An", is_local=True, local_players=local_players)
    assert room.is_local is True
    assert room.status == "playing"
    assert len(room.players) == 2
    assert room.game_state is not None
    assert room.game_state["current_player"] == 0

    # In local multiplayer, host token can submit moves on behalf of current turn player
    room, event = RoomService.process_action(room.code, token, {"type": "place_piece", "row": 7, "col": 7})
    assert room.game_state["current_player"] == 1
    assert room.game_state["grid"][7][7] == "X"

    # Next move
    room, event = RoomService.process_action(room.code, token, {"type": "place_piece", "row": 7, "col": 8})
    assert room.game_state["current_player"] == 0
    assert room.game_state["grid"][7][8] == "O"

def test_transfer_host_and_disband():
    room, host, token1 = RoomService.create_room("caro", "Host1", is_local=False)
    room, p2, token2 = RoomService.join_room(room.code, "Player2")
    assert host.is_host is True
    assert p2.is_host is False

    # Transfer host to Player 2
    room, old_h, new_h = RoomService.transfer_host(room.code, token1, p2.player_index)
    assert old_h.is_host is False
    assert new_h.is_host is True

    # Now Player 2 (new host) leaves without transferring -> room abandoned
    room, msg = RoomService.leave_room(room.code, token2)
    assert room.status == "abandoned"
    assert "Chủ phòng" in msg
