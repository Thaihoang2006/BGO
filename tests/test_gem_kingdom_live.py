import urllib.request
import json
import time

BASE_URL = "http://127.0.0.1:5500"

def post(path, data):
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}{path}", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get(path):
    req = urllib.request.Request(f"{BASE_URL}{path}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def main():
    print("Testing Gem Kingdom (Splendor) on Live Server Port 5500...")

    # 1. Rules check
    rules_res = get("/api/games/gem_kingdom/rules")
    assert "Splendor" in rules_res["rules"]["title"]
    assert len(rules_res["rules"]["setup"]) >= 4
    print("[PASS] Gem Kingdom Splendor rules served successfully")

    # 2. Local 3-player match
    local_res = post("/api/rooms", {
        "game_type": "gem_kingdom",
        "player_name": "KỳThủ1",
        "is_local": True,
        "local_players": [
            {"name": "Alice", "color": "#FF9966", "symbol": "P1"},
            {"name": "Bob", "color": "#FFE1BA", "symbol": "P2"},
            {"name": "Charlie", "color": "#BE807D", "symbol": "P3"}
        ]
    })
    room_code = local_res["room_code"]
    token = local_res["participant_token"]
    state = local_res["room"]["game_state"]
    # 3 players: 5 of each regular gem, 4 nobles (3 + 1)
    assert state["bank"]["ruby"] == 5
    assert state["bank"]["gold"] == 5
    assert len(state["nobles"]) == 4
    assert len(state["players"]) == 3
    print(f"[PASS] Local 3-Player Match created: {room_code} (5 gems each, 4 nobles)")

    # P1 takes 3 gems: ruby, sapphire, emerald
    m1 = post(f"/api/rooms/{room_code}/action", {
        "participant_token": token,
        "action": {"type": "take_three_gems", "gems": ["ruby", "sapphire", "emerald"]}
    })
    assert m1["success"] is True
    assert m1["room"]["game_state"]["current_player"] == 1
    assert m1["room"]["game_state"]["players"][0]["tokens"]["ruby"] == 1
    print("[PASS] P1 took 3 gems (ruby, sapphire, emerald)")

    # P2 takes 2 emeralds (bank had 4 left -> valid)
    m2 = post(f"/api/rooms/{room_code}/action", {
        "participant_token": token,
        "action": {"type": "take_two_gems", "gem": "emerald"}
    })
    assert m2["success"] is True
    assert m2["room"]["game_state"]["current_player"] == 2
    assert m2["room"]["game_state"]["players"][1]["tokens"]["emerald"] == 2
    print("[PASS] P2 took 2 emeralds (rule of 4 validated)")

    # P3 reserves card from Level 1
    card_id = m2["room"]["game_state"]["board"]["1"][0]["id"]
    m3 = post(f"/api/rooms/{room_code}/action", {
        "participant_token": token,
        "action": {"type": "reserve_card", "source": "board", "level": 1, "card_id": card_id}
    })
    assert m3["success"] is True
    assert m3["room"]["game_state"]["current_player"] == 0 # Back to P1
    assert len(m3["room"]["game_state"]["players"][2]["reserved_cards"]) == 1
    assert m3["room"]["game_state"]["players"][2]["tokens"]["gold"] == 1
    print("[PASS] P3 reserved Level 1 card and gained 1 Gold Token")

    print("\nALL GEM KINGDOM LIVE SERVER TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
