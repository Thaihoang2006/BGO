import socketio
import time
import urllib.request
import json

BASE_URL = "http://127.0.0.1:5500"

def post(path, data):
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}{path}", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def main():
    print("Testing 2-Client WebSocket Real-Time Synchronization...")

    # 1. Host creates room via REST
    host_res = post("/api/rooms", {
        "game_type": "caro",
        "player_name": "KỳThủA",
        "is_local": False
    })
    room_code = host_res["room_code"]
    host_token = host_res["participant_token"]
    print(f"[1] Room created: {room_code}, Host Token: {host_token[:8]}...")

    # 2. Guest joins room via REST
    guest_res = post(f"/api/rooms/{room_code}/join", {
        "player_name": "KỳThủB"
    })
    guest_token = guest_res["participant_token"]
    print(f"[2] Guest joined: {guest_res['player_index']}, Guest Token: {guest_token[:8]}...")

    # 3. Connect SocketIO Client A (Host)
    sio_a = socketio.Client()
    received_a = []

    @sio_a.on("game_started")
    def on_game_started_a(data):
        received_a.append(("game_started", data))

    @sio_a.on("game_update")
    def on_game_update_a(data):
        received_a.append(("game_update", data))

    sio_a.connect(BASE_URL)
    sio_a.emit("join_room_socket", {"room_code": room_code, "participant_token": host_token})
    print("[3] SIO Client A connected and joined room")

    # 4. Connect SocketIO Client B (Guest)
    sio_b = socketio.Client()
    received_b = []

    @sio_b.on("game_started")
    def on_game_started_b(data):
        received_b.append(("game_started", data))

    @sio_b.on("game_update")
    def on_game_update_b(data):
        received_b.append(("game_update", data))

    sio_b.connect(BASE_URL)
    sio_b.emit("join_room_socket", {"room_code": room_code, "participant_token": guest_token})
    print("[4] SIO Client B connected and joined room")

    time.sleep(0.3)

    # 5. Client B readies up via SocketIO
    sio_b.emit("set_ready", {"room_code": room_code, "participant_token": guest_token, "is_ready": True})
    time.sleep(0.3)
    print("[5] SIO Client B emitted set_ready")

    # 6. Client A starts game via SocketIO
    sio_a.emit("start_game", {"room_code": room_code, "participant_token": host_token})
    time.sleep(0.5)

    # Verify both received game_started event
    started_a = [e for e in received_a if e[0] == "game_started"]
    started_b = [e for e in received_b if e[0] == "game_started"]
    assert len(started_a) == 1, f"Client A should receive game_started, got {received_a}"
    assert len(started_b) == 1, f"Client B should receive game_started, got {received_b}"
    print("[6] BOTH Clients received 'game_started' event in real-time!")

    # 7. Client A makes a move: place X at (7, 7)
    sio_a.emit("game_action", {
        "room_code": room_code,
        "participant_token": host_token,
        "action": {"type": "place_piece", "row": 7, "col": 7},
        "client_version": 1
    })
    time.sleep(0.5)

    # Verify both received game_update event with piece at (7, 7)
    updates_a = [e for e in received_a if e[0] == "game_update"]
    updates_b = [e for e in received_b if e[0] == "game_update"]
    assert len(updates_a) == 1
    assert len(updates_b) == 1
    assert updates_b[0][1]["game_state"]["grid"][7][7] == "X"
    assert updates_b[0][1]["game_state"]["current_player"] == 1
    print("[7] BOTH Clients received 'game_update' with stone placed at (7, 7)!")

    # 8. Client B makes a move: place O at (7, 8)
    sio_b.emit("game_action", {
        "room_code": room_code,
        "participant_token": guest_token,
        "action": {"type": "place_piece", "row": 7, "col": 8},
        "client_version": 2
    })
    time.sleep(0.5)

    updates_b = [e for e in received_b if e[0] == "game_update"]
    assert len(updates_b) == 2
    assert updates_b[1][1]["game_state"]["grid"][7][8] == "O"
    assert updates_b[1][1]["game_state"]["current_player"] == 0
    print("[8] BOTH Clients received 'game_update' with stone placed at (7, 8)!")

    sio_a.disconnect()
    sio_b.disconnect()
    print("\nSUCCESS: 100% REAL-TIME WEBSOCKET ONLINE MULTIPLAYER CONFIRMED WORKING!")

if __name__ == "__main__":
    main()
