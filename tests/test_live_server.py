import urllib.request
import urllib.error
import json
import sys

BASE_URL = "http://127.0.0.1:5500"

def get(path, headers=None):
    req = urllib.request.Request(f"{BASE_URL}{path}", headers=headers or {})
    with urllib.request.urlopen(req) as resp:
        return resp.status, resp.read().decode("utf-8")

def post(path, data, headers=None):
    body = json.dumps(data).encode("utf-8")
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(f"{BASE_URL}{path}", data=body, headers=h)
    with urllib.request.urlopen(req) as resp:
        return resp.status, resp.read().decode("utf-8")

def main():
    print("Testing live BGO server...")

    # 1. Health & Home
    status, html = get("/")
    assert status == 200, f"Expected 200, got {status}"
    assert "BGO" in html
    assert "Play Together" in html or "Board Games Online" in html
    print("[PASS] GET / (Home page HTML served OK)")

    status, health_json = get("/api/health")
    assert status == 200
    health = json.loads(health_json)
    assert health["status"] == "ok"
    print("[PASS] GET /api/health OK")

    # 2. Games & Rules
    status, games_json = get("/api/games")
    games_data = json.loads(games_json)
    assert len(games_data["games"]) == 4
    caro_meta = next(g for g in games_data["games"] if g["id"] == "caro")
    assert caro_meta["status"] == "ready"
    print("[PASS] GET /api/games (4 board games configured) OK")

    status, rules_json = get("/api/games/caro/rules")
    rules_data = json.loads(rules_json)
    assert rules_data["game_type"] == "caro"
    assert "Gomoku" in rules_data["rules"]["title"]
    print("[PASS] GET /api/games/caro/rules OK")

    # 3. Local Multiplayer match
    status, local_res_str = post("/api/rooms", {
        "game_type": "caro",
        "player_name": "Kỳ thủ 1",
        "is_local": True,
        "local_players": [
            {"name": "Kỳ thủ 1", "color": "#FF9966", "symbol": "X"},
            {"name": "Kỳ thủ 2", "color": "#FFE1BA", "symbol": "O"}
        ]
    })
    assert status == 201
    local_data = json.loads(local_res_str)
    assert local_data["success"] is True
    local_code = local_data["room_code"]
    local_token = local_data["participant_token"]
    assert local_data["room"]["is_local"] is True
    assert local_data["room"]["status"] == "playing"
    print(f"[PASS] Local Multiplayer Room created: {local_code}")

    # Move 1 (Local)
    status, m1_str = post(f"/api/rooms/{local_code}/action", {
        "participant_token": local_token,
        "action": {"type": "place_piece", "row": 7, "col": 7}
    })
    assert status == 200
    m1 = json.loads(m1_str)
    assert m1["room"]["game_state"]["grid"][7][7] == "X"
    assert m1["room"]["game_state"]["current_player"] == 1
    print("[PASS] Local Move 1 (7, 7) placed by Player 0 (X)")

    # Move 2 (Local)
    status, m2_str = post(f"/api/rooms/{local_code}/action", {
        "participant_token": local_token,
        "action": {"type": "place_piece", "row": 7, "col": 8}
    })
    assert status == 200
    m2 = json.loads(m2_str)
    assert m2["room"]["game_state"]["grid"][7][8] == "O"
    assert m2["room"]["game_state"]["current_player"] == 0
    print("[PASS] Local Move 2 (7, 8) placed by Player 1 (O)")

    # 4. Online Multiplayer match (2 distinct players)
    # Player A creates room
    status, res_a_str = post("/api/rooms", {
        "game_type": "caro",
        "player_name": "HostAlpha",
        "is_local": False
    })
    assert status == 201
    data_a = json.loads(res_a_str)
    online_code = data_a["room_code"]
    token_a = data_a["participant_token"]
    print(f"[PASS] Online Room created: {online_code} by HostAlpha")

    # Player B joins room
    status, res_b_str = post(f"/api/rooms/{online_code}/join", {
        "player_name": "GuestBeta"
    })
    assert status == 200
    data_b = json.loads(res_b_str)
    token_b = data_b["participant_token"]
    assert token_a != token_b
    print(f"[PASS] GuestBeta joined room {online_code}")

    # Ready up & Start
    status, ready_res = post(f"/api/rooms/{online_code}/ready", {
        "participant_token": token_b,
        "is_ready": True
    })
    assert status == 200, f"Ready failed: {ready_res}"

    status, start_res = post(f"/api/rooms/{online_code}/start", {
        "participant_token": token_a
    })
    assert status == 200, f"Start failed: {start_res}"

    # Verify match started
    status, room_check_str = get(f"/api/rooms/{online_code}", headers={"X-Participant-Token": token_a})
    room_check = json.loads(room_check_str)["room"]
    assert room_check["status"] == "playing"
    assert room_check["game_state"]["current_player"] == 0
    curr_v = room_check["state_version"]
    print(f"[PASS] Online Match started, version = {curr_v}")

    # Play moves until HostAlpha wins with 5 horizontally: row 7, cols 3..7
    for col in range(3, 7):
        # HostAlpha move
        status, move_a = post(f"/api/rooms/{online_code}/action", {
            "participant_token": token_a,
            "action": {"type": "place_piece", "row": 7, "col": col},
            "client_version": curr_v
        })
        assert status == 200, f"Host move failed: {move_a}"
        curr_v += 1

        # GuestBeta move
        status, move_b = post(f"/api/rooms/{online_code}/action", {
            "participant_token": token_b,
            "action": {"type": "place_piece", "row": 8, "col": col},
            "client_version": curr_v
        })
        assert status == 200, f"Guest move failed: {move_b}"
        curr_v += 1

    # Winning move for HostAlpha at (7, 7)
    status, win_res_str = post(f"/api/rooms/{online_code}/action", {
        "participant_token": token_a,
        "action": {"type": "place_piece", "row": 7, "col": 7},
        "client_version": curr_v
    })
    assert status == 200
    win_data = json.loads(win_res_str)
    assert win_data["event"]["game_over"] is True
    assert win_data["room"]["status"] == "finished"
    assert win_data["room"]["winner"]["symbol"] == "X"
    assert win_data["room"]["winner"]["name"] == "HostAlpha"
    assert len(win_data["room"]["winner"]["winning_line"]) == 5
    assert win_data["room"]["session_scores"].get("0") == 1
    print("[PASS] HostAlpha won with 5 in a row! Session score 1-0 updated!")

    # 5. Mutual Rematch Flow
    # HostAlpha requests rematch
    status, rem1_str = post(f"/api/rooms/{online_code}/rematch/request", {
        "participant_token": token_a
    })
    assert status == 200
    rem1 = json.loads(rem1_str)
    assert rem1["restarted"] is False
    print("[PASS] HostAlpha requested rematch (waiting for GuestBeta)")

    # GuestBeta accepts rematch
    status, rem2_str = post(f"/api/rooms/{online_code}/rematch/request", {
        "participant_token": token_b
    })
    assert status == 200
    rem2 = json.loads(rem2_str)
    assert rem2["restarted"] is True
    assert rem2["room"]["status"] == "playing"
    assert rem2["room"]["session_scores"].get("0") == 1
    print("[PASS] GuestBeta accepted rematch! Match restarted with score 1-0 preserved!")

    # 6. Switch Game in Room
    status, sw_str = post(f"/api/rooms/{online_code}/switch_game", {
        "participant_token": token_a,
        "new_game_type": "ludo"
    })
    assert status == 200
    sw_data = json.loads(sw_str)
    assert sw_data["room"]["game_type"] == "ludo"
    assert sw_data["room"]["status"] == "waiting"
    print("[PASS] Host successfully switched game in room to 'ludo'!")

    # Switch to monopoly
    status, sw2_str = post(f"/api/rooms/{online_code}/switch_game", {
        "participant_token": token_a,
        "new_game_type": "monopoly"
    })
    assert status == 200
    sw2_data = json.loads(sw2_str)
    assert sw2_data["room"]["game_type"] == "monopoly"
    print("[PASS] Host successfully switched game in room to 'monopoly'!")

    # 7. Return to lobby test
    status, ret_str = post(f"/api/rooms/{online_code}/return_to_lobby", {
        "participant_token": token_a
    })
    assert status == 200
    ret_data = json.loads(ret_str)
    assert ret_data["room"]["status"] == "waiting"
    assert ret_data["room"]["game_state"] is None
    print("[PASS] Player successfully returned to lobby via /return_to_lobby!")

    print("\nALL LIVE TESTS PASSED SUCCESSFULLY! ")

if __name__ == "__main__":
    main()
