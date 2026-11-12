import pytest
from backend.games.ludo.engine import LudoEngine

@pytest.fixture
def engine():
    return LudoEngine()

@pytest.fixture
def initial_state(engine):
    players = [
        {"player_index": 0, "name": "RedPlayer", "color": "#FF5A36"},
        {"player_index": 1, "name": "BluePlayer", "color": "#3A86FF"}
    ]
    return engine.create_initial_state(players)

def test_initial_state(initial_state):
    assert initial_state["game_type"] == "ludo"
    assert len(initial_state["players"]) == 2
    assert initial_state["current_player"] == 0
    assert initial_state["phase"] == "roll"
    assert len(initial_state["players"][0]["horses"]) == 4
    for h in initial_state["players"][0]["horses"]:
        assert h["status"] == "stable"

def test_roll_and_deploy_horse(engine, initial_state):
    state = initial_state
    # Roll dice
    state, event = engine.apply_action(state, 0, {"type": "roll_dice"})
    assert event["dice"] in range(1, 7)

    # Force a roll of 6 to test deployment
    state["current_player"] = 0
    state["dice_value"] = 6
    state["bonus_roll"] = True
    valid = engine._get_valid_horses(state, 0, 6)
    assert len(valid) == 4 # All 4 stable horses can deploy on 6
    assert len(engine._get_valid_horses(state, 0, 1)) == 4 # All 4 stable horses can also deploy on 1 (Vietnamese rule)
    state["valid_horse_ids"] = valid
    state["phase"] = "select_horse"

    # Deploy horse 0
    state, event = engine.apply_action(state, 0, {"type": "move_horse", "horse_id": 0})
    h0 = state["players"][0]["horses"][0]
    assert h0["status"] == "on_track"
    assert h0["step"] == state["players"][0]["start_step"]
    # On 6, bonus roll is granted!
    assert state["current_player"] == 0
    assert state["phase"] == "roll"

def test_kick_opponent(engine, initial_state):
    state = initial_state
    # Place player 1's horse at step 5
    p1 = state["players"][1]
    p1["horses"][0]["status"] = "on_track"
    p1["horses"][0]["step"] = 5
    p1["horses"][0]["distance_walked"] = 5

    # Player 0's horse is at step 2, dice is 3 -> advances to step 5!
    p0 = state["players"][0]
    p0["horses"][0]["status"] = "on_track"
    p0["horses"][0]["step"] = 2
    p0["horses"][0]["distance_walked"] = 2

    state["dice_value"] = 3
    state["bonus_roll"] = False
    state["phase"] = "select_horse"
    state["valid_horse_ids"] = [0]

    state, event = engine.apply_action(state, 0, {"type": "move_horse", "horse_id": 0})

    # P0 is now at step 5
    assert state["players"][0]["horses"][0]["step"] == 5
    # P1's horse was kicked back to stable!
    assert state["players"][1]["horses"][0]["status"] == "stable"
    assert state["players"][1]["horses"][0]["step"] == 0
    assert event["kicked"]["victim_player_index"] == 1
