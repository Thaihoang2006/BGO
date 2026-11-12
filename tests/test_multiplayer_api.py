import pytest
from backend.app import create_app
from backend.database import db

@pytest.fixture
def client():
    # Setup test DB
    test_db = "bgo_api_test.db"
    db.db_url = f"sqlite:///{test_db}"
    db.is_mysql = False
    db.create_tables()

    db.execute("DELETE FROM match_events")
    db.execute("DELETE FROM room_players")
    db.execute("DELETE FROM rooms")

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

    db.execute("DELETE FROM match_events")
    db.execute("DELETE FROM room_players")
    db.execute("DELETE FROM rooms")

def test_api_two_player_caro_match(client):
    # 1. Player 1 creates room
    res1 = client.post("/api/rooms", json={
        "game_type": "caro",
        "player_name": "Minh",
        "is_local": False
    })
    assert res1.status_code == 201
    data1 = res1.get_json()
    assert data1["success"] is True
    room_code = data1["room_code"]
    p1_token = data1["participant_token"]
    assert data1["player_index"] == 0

    # 2. Player 2 joins room
    res2 = client.post(f"/api/rooms/{room_code}/join", json={
        "player_name": "Lan"
    })
    assert res2.status_code == 200
    data2 = res2.get_json()
    assert data2["success"] is True
    p2_token = data2["participant_token"]
    assert data2["player_index"] == 1
    assert data2["room"]["player_count"] == 2

    # 3. Player 2 sets ready via room service
    from backend.services.room_service import RoomService
    RoomService.set_player_ready(room_code, p2_token, True)

    # 4. Player 1 starts game
    RoomService.start_game(room_code, p1_token)

    # Check room state
    res_room = client.get(f"/api/rooms/{room_code}")
    assert res_room.status_code == 200
    room_info = res_room.get_json()["room"]
    assert room_info["status"] == "playing"
    assert room_info["game_state"]["current_player"] == 0
    assert room_info["state_version"] == 1

    # 5. Play moves: Player 1 lines up 5 stones on row 7
    # P1: (7, 3), (7, 4), (7, 5), (7, 6), (7, 7)
    # P2: (8, 3), (8, 4), (8, 5), (8, 6)
    curr_version = 1
    for i in range(4):
        # P1 move
        res_move1 = client.post(f"/api/rooms/{room_code}/action", json={
            "participant_token": p1_token,
            "action": {"type": "place_piece", "row": 7, "col": i + 3},
            "client_version": curr_version
        })
        assert res_move1.status_code == 200
        curr_version += 1

        # P2 move
        res_move2 = client.post(f"/api/rooms/{room_code}/action", json={
            "participant_token": p2_token,
            "action": {"type": "place_piece", "row": 8, "col": i + 3},
            "client_version": curr_version
        })
        assert res_move2.status_code == 200
        curr_version += 1

    # 6. P1 plays winning 5th stone at (7, 7)
    res_win = client.post(f"/api/rooms/{room_code}/action", json={
        "participant_token": p1_token,
        "action": {"type": "place_piece", "row": 7, "col": 7},
        "client_version": curr_version
    })
    assert res_win.status_code == 200
    win_data = res_win.get_json()
    assert win_data["event"]["game_over"] is True
    assert win_data["room"]["status"] == "finished"
    assert win_data["room"]["winner"]["symbol"] == "X"
    assert win_data["room"]["winner"]["player_index"] == 0
    assert len(win_data["room"]["winner"]["winning_line"]) == 5

    # 7. Restart match
    res_restart = client.post(f"/api/rooms/{room_code}/restart", json={
        "participant_token": p1_token
    })
    assert res_restart.status_code == 200
    restart_data = res_restart.get_json()
    assert restart_data["room"]["status"] == "playing"
    assert restart_data["room"]["game_state"]["moves_count"] == 0
    assert restart_data["room"]["winner"] is None
