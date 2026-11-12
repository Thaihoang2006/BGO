import pytest
from backend.services.room_service import RoomService
from backend.database import db

@pytest.fixture(autouse=True)
def setup_db():
    db.db_url = "sqlite:///bgo_gem_test.db"
    db.is_mysql = False
    db.create_tables()
    db.execute("DELETE FROM match_events")
    db.execute("DELETE FROM room_players")
    db.execute("DELETE FROM rooms")
    yield
    db.execute("DELETE FROM match_events")
    db.execute("DELETE FROM room_players")
    db.execute("DELETE FROM rooms")

def test_gem_kingdom_local_match():
    local_players = [
        {"name": "Alice", "color": "#FF9966"},
        {"name": "Bob", "color": "#FFE1BA"}
    ]
    room, host, token = RoomService.create_room("gem_kingdom", "Alice", is_local=True, local_players=local_players)
    assert room.is_local is True
    assert room.game_type == "gem_kingdom"
    assert room.status == "playing"
    assert room.game_state["bank"]["emerald"] == 4
    assert len(room.game_state["nobles"]) == 3

    # Turn 1: Alice takes 3 gems (ruby, sapphire, emerald)
    action1 = {"type": "take_three_gems", "gems": ["ruby", "sapphire", "emerald"]}
    room, event = RoomService.process_action(room.code, token, action1)
    assert room.game_state["current_player"] == 1
    assert room.game_state["players"][0]["tokens"]["ruby"] == 1

    # Turn 2: Bob takes 2 diamonds
    action2 = {"type": "take_two_gems", "gem": "diamond"}
    room, event = RoomService.process_action(room.code, token, action2)
    assert room.game_state["current_player"] == 0
    assert room.game_state["players"][1]["tokens"]["diamond"] == 2
