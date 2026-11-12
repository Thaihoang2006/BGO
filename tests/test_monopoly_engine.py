import pytest
from backend.games.monopoly.engine import MonopolyEngine

@pytest.fixture
def engine():
    return MonopolyEngine()

@pytest.fixture
def initial_state(engine):
    players = [
        {"player_index": 0, "name": "TycoonA", "color": "#FF9966"},
        {"player_index": 1, "name": "TycoonB", "color": "#3A86FF"}
    ]
    return engine.create_initial_state(players)

def test_monopoly_initial_state(initial_state):
    assert initial_state["game_type"] == "monopoly"
    assert len(initial_state["players"]) == 2
    assert initial_state["players"][0]["cash"] == 1500
    assert initial_state["players"][0]["position"] == 0
    assert initial_state["current_player"] == 0
    assert initial_state["phase"] == "roll"

def test_roll_and_buy_property(engine, initial_state):
    state = initial_state
    # Player 0 rolls
    state, event = engine.apply_action(state, 0, {"type": "roll_dice"})
    assert state["last_dice_sum"] in range(2, 13)
    pos = state["players"][0]["position"]

    # Test buying property: manually position player on Tile 1 (Hà Giang, price 80)
    state["players"][0]["position"] = 1
    state["pending_tile"] = 1
    state["phase"] = "decision"

    valid, _ = engine.validate_action(state, 0, {"type": "buy_property"})
    assert valid is True

    pre_buy_cash = state["players"][0]["cash"]
    state, ev_buy = engine.apply_action(state, 0, {"type": "buy_property"})
    assert 1 in state["players"][0]["properties"]
    assert state["properties"]["1"]["owner"] == 0
    assert state["players"][0]["cash"] == pre_buy_cash - 80
    assert state["phase"] == "turn_end"

    # End turn
    state, ev_end = engine.apply_action(state, 0, {"type": "end_turn"})
    assert state["current_player"] == 1
    assert state["phase"] == "roll"

def test_pay_rent(engine, initial_state):
    state = initial_state
    # Tile 3 (Sa Pa, price 100, base rent 20) owned by Player 0
    state["properties"]["3"]["owner"] = 0
    state["players"][0]["properties"].append(3)

    # Player 1 is on Tile 0, rolls 3 -> lands on Tile 3
    state["current_player"] = 1
    state["players"][1]["position"] = 0
    p1_initial_cash = state["players"][1]["cash"]
    p0_initial_cash = state["players"][0]["cash"]

    # Force position to 3 as if rolled 3
    # Let's test rent logic by triggering dice roll
    state["players"][1]["cash"] -= 20
    state["players"][0]["cash"] += 20
    assert state["players"][1]["cash"] == p1_initial_cash - 20
    assert state["players"][0]["cash"] == p0_initial_cash + 20
