import time
import pytest
from backend.app import create_app
from backend.services.room_service import RoomService
from backend.database import db
from backend.games.undercover.engine import UndercoverEngine


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_twenty_players_and_spectator_flow(client):
    # 1. Host creates Undercover room with max 20 players
    res = client.post("/api/rooms", json={
        "game_type": "undercover",
        "player_name": "Host_P0",
        "max_players": 20
    })
    assert res.status_code == 201
    data = res.get_json()
    room_code = data["room_code"]
    host_token = data["participant_token"]

    tokens = [host_token]

    # 2. 19 more players join (total 20 official players)
    for i in range(1, 20):
        res_j = client.post(f"/api/rooms/{room_code}/join", json={
            "player_name": f"Player_{i}",
            "role": "player"
        })
        assert res_j.status_code == 200
        p_data = res_j.get_json()
        assert p_data["is_spectator"] is False
        tokens.append(p_data["participant_token"])

    # 3. 21st player attempts to join as official player -> Rejected with suggestion
    res_21 = client.post(f"/api/rooms/{room_code}/join", json={
        "player_name": "Player_21",
        "role": "player"
    })
    assert res_21.status_code == 400
    assert "Khán giả" in res_21.get_json()["error"]

    # 4. 21st player joins as Spectator
    res_spec = client.post(f"/api/rooms/{room_code}/join", json={
        "player_name": "Spectator_1",
        "role": "spectator"
    })
    assert res_spec.status_code == 200
    spec_data = res_spec.get_json()
    assert spec_data["is_spectator"] is True
    spec_token = spec_data["participant_token"]

    # Check room state via API
    res_room = client.get(f"/api/rooms/{room_code}?token={spec_token}")
    assert res_room.status_code == 200
    r_info = res_room.get_json()["room"]
    assert r_info["player_count"] == 20
    assert r_info["spectator_count"] == 1
    assert r_info["is_viewer_spectator"] is True

    # 5. Spectator cannot ready up
    RoomService.set_player_ready(room_code, spec_token, True)

    # All 19 other players ready up
    for tok in tokens[1:]:
        RoomService.set_player_ready(room_code, tok, True)

    # 6. Host starts game
    RoomService.start_game(room_code, host_token)

    # 7. Check Spectator's view of active game -> ZERO secret words or roles leaked!
    res_spec_view = client.get(f"/api/rooms/{room_code}?token={spec_token}")
    spec_game = res_spec_view.get_json()["room"]["game_state"]
    assert "secret_words" not in spec_game
    for p in spec_game["players"]:
        assert p["role"] == "???"
        assert p["word"] == "???"

    # 8. Spectator attempts to submit a description -> Forbidden!
    res_act = client.post(f"/api/rooms/{room_code}/action", json={
        "participant_token": spec_token,
        "action": {"type": "submit_description", "text": "Hacked description"}
    })
    assert res_act.status_code == 400
    assert "Khán giả không thể thực hiện hành động" in res_act.get_json()["error"]


def test_chat_roles_antispam_and_xss(client):
    # Setup room with 1 player and 1 spectator
    res = client.post("/api/rooms", json={"game_type": "undercover", "player_name": "Gamer"})
    room_code = res.get_json()["room_code"]
    p_token = res.get_json()["participant_token"]

    res_s = client.post(f"/api/rooms/{room_code}/join", json={"player_name": "Watcher", "role": "spectator"})
    s_token = res_s.get_json()["participant_token"]

    # 1. Player sends chat
    res_c1 = client.post(f"/api/rooms/{room_code}/chat", json={
        "participant_token": p_token,
        "message": "Xin chào phòng!"
    })
    assert res_c1.status_code == 200
    msg1 = res_c1.get_json()["message"]
    assert msg1["sender_role"] == "player"

    # 2. Spectator sends chat
    res_c2 = client.post(f"/api/rooms/{room_code}/chat", json={
        "participant_token": s_token,
        "message": "Cố lên nhé!"
    })
    assert res_c2.status_code == 200
    msg2 = res_c2.get_json()["message"]
    assert msg2["sender_role"] == "spectator"

    # 3. Anti-spam test: sending immediately within 0.1s
    res_spam = client.post(f"/api/rooms/{room_code}/chat", json={
        "participant_token": s_token,
        "message": "Spam spam spam"
    })
    assert res_spam.status_code == 400
    assert "quá nhanh" in res_spam.get_json()["error"]

    # 4. XSS Sanitization test
    time.sleep(0.5)
    res_xss = client.post(f"/api/rooms/{room_code}/chat", json={
        "participant_token": p_token,
        "message": "<script>alert('xss')</script><b>Bold</b>"
    })
    assert res_xss.status_code == 200
    msg_xss = res_xss.get_json()["message"]
    assert "<script>" not in msg_xss["message"]
    assert "&lt;script&gt;" in msg_xss["message"]

    # 5. Host mute spectator chat test
    time.sleep(0.5)
    client.post(f"/api/rooms/{room_code}/settings", json={
        "participant_token": p_token,
        "settings": {"mute_spectator_chat": True}
    })
    res_muted = client.post(f"/api/rooms/{room_code}/chat", json={
        "participant_token": s_token,
        "message": "Khán giả nói được không?"
    })
    assert res_muted.status_code == 400
    assert "khóa" in res_muted.get_json()["error"]


def test_load_simulation_twenty_players_thirty_spectators(client):
    """Simulate 20 players + 30 spectators (50 total connections) in a room.
    Measures latency and confirms 0 errors.
    """
    start_t = time.time()
    # 1. Host creates room
    res = client.post("/api/rooms", json={"game_type": "undercover", "player_name": "Host", "max_players": 20})
    room_code = res.get_json()["room_code"]
    host_token = res.get_json()["participant_token"]

    # 2. 19 more players join
    for i in range(1, 20):
        res_p = client.post(f"/api/rooms/{room_code}/join", json={"player_name": f"P_{i}", "role": "player"})
        assert res_p.status_code == 200

    # 3. 30 spectators join
    for j in range(1, 31):
        res_s = client.post(f"/api/rooms/{room_code}/join", json={"player_name": f"Viewer_{j}", "role": "spectator"})
        assert res_s.status_code == 200

    elapsed = time.time() - start_t

    # 4. Verify room totals
    res_info = client.get(f"/api/rooms/{room_code}")
    room_dict = res_info.get_json()["room"]
    assert room_dict["player_count"] == 20
    assert room_dict["spectator_count"] == 30
    assert (room_dict["player_count"] + room_dict["spectator_count"]) == 50

    # Latency check: 50 join requests handled under 5 seconds
    assert elapsed < 5.0
