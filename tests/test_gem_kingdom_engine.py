import pytest
from backend.games.gem_kingdom.engine import GemKingdomEngine

@pytest.fixture
def engine():
    return GemKingdomEngine()

@pytest.fixture
def initial_state(engine):
    players = [
        {"player_index": 0, "name": "Alice", "color": "#FF9966"},
        {"player_index": 1, "name": "Bob", "color": "#FFE1BA"}
    ]
    return engine.create_initial_state(players)

def test_initial_state(initial_state):
    assert initial_state["game_type"] == "gem_kingdom"
    assert initial_state["status"] == "playing"
    assert initial_state["current_player"] == 0
    # 2 players: 4 of each regular gem, 5 gold
    for g in ["emerald", "diamond", "sapphire", "onyx", "ruby"]:
        assert initial_state["bank"][g] == 4
    assert initial_state["bank"]["gold"] == 5
    # 2 players: 3 nobles (2 + 1)
    assert len(initial_state["nobles"]) == 3
    # 12 cards on board (4 per level)
    assert len(initial_state["board"]["1"]) == 4
    assert len(initial_state["board"]["2"]) == 4
    assert len(initial_state["board"]["3"]) == 4

def test_take_three_gems(engine, initial_state):
    # Valid take 3 distinct gems
    action = {"type": "take_three_gems", "gems": ["ruby", "sapphire", "emerald"]}
    valid, msg = engine.validate_action(initial_state, 0, action)
    assert valid is True

    new_state, _ = engine.apply_action(initial_state, 0, action)
    assert new_state["bank"]["ruby"] == 3
    assert new_state["bank"]["sapphire"] == 3
    assert new_state["bank"]["emerald"] == 3
    assert new_state["players"][0]["tokens"]["ruby"] == 1
    assert new_state["players"][0]["tokens"]["sapphire"] == 1
    assert new_state["players"][0]["tokens"]["emerald"] == 1
    assert new_state["current_player"] == 1

    # Invalid: duplicate colors
    invalid_action = {"type": "take_three_gems", "gems": ["ruby", "ruby", "emerald"]}
    valid, msg = engine.validate_action(new_state, 1, invalid_action)
    assert valid is False

    # Invalid: taking gold
    invalid_gold = {"type": "take_three_gems", "gems": ["ruby", "gold", "emerald"]}
    valid, msg = engine.validate_action(new_state, 1, invalid_gold)
    assert valid is False

def test_take_two_gems_rule_of_four(engine, initial_state):
    # Bank has 4 emeralds -> taking 2 is allowed
    action = {"type": "take_two_gems", "gem": "emerald"}
    valid, msg = engine.validate_action(initial_state, 0, action)
    assert valid is True

    state1, _ = engine.apply_action(initial_state, 0, action)
    assert state1["bank"]["emerald"] == 2
    assert state1["players"][0]["tokens"]["emerald"] == 2

    # Now bank has 2 emeralds -> taking 2 emeralds is NOT allowed (< 4)
    valid, msg = engine.validate_action(state1, 1, action)
    assert valid is False
    assert "ít nhất 4 viên" in msg

def test_reserve_card_and_gain_gold(engine, initial_state):
    card_to_reserve = initial_state["board"]["1"][0]
    action = {
        "type": "reserve_card",
        "source": "board",
        "level": 1,
        "card_id": card_to_reserve["id"]
    }
    valid, msg = engine.validate_action(initial_state, 0, action)
    assert valid is True

    new_state, _ = engine.apply_action(initial_state, 0, action)
    assert len(new_state["players"][0]["reserved_cards"]) == 1
    assert new_state["players"][0]["reserved_cards"][0]["id"] == card_to_reserve["id"]
    # Gained 1 gold token
    assert new_state["players"][0]["tokens"]["gold"] == 1
    assert new_state["bank"]["gold"] == 4
    # Board refilled to 4 cards
    assert len(new_state["board"]["1"]) == 4

def test_max_3_reserved_cards(engine, initial_state):
    state = initial_state
    # Reserve 3 cards
    for i in range(3):
        card = state["board"]["1"][0]
        state["current_player"] = 0
        state, _ = engine.apply_action(state, 0, {
            "type": "reserve_card", "source": "board", "level": 1, "card_id": card["id"]
        })

    assert len(state["players"][0]["reserved_cards"]) == 3
    state["current_player"] = 0
    # Try to reserve 4th card -> rejected
    card4 = state["board"]["1"][0]
    valid, msg = engine.validate_action(state, 0, {
        "type": "reserve_card", "source": "board", "level": 1, "card_id": card4["id"]
    })
    assert valid is False
    assert "tối đa 3 lá" in msg

def test_buy_card_with_discount_and_gold(engine, initial_state):
    state = initial_state
    # Give player 0: 2 ruby tokens, 1 gold token, and 1 emerald bonus
    state["players"][0]["tokens"]["ruby"] = 2
    state["players"][0]["tokens"]["gold"] = 1
    state["players"][0]["bonuses"]["emerald"] = 1

    # Fake card requiring 2 ruby, 2 emerald (discount makes emerald cost 1)
    test_card = {
        "id": "c_test", "level": 1, "gem": "sapphire", "points": 1,
        "cost": {"ruby": 2, "emerald": 2}
    }
    state["board"]["1"][0] = test_card

    # Player has 2 ruby (covers ruby), 0 emerald tokens + 1 emerald bonus -> deficit = 1 emerald.
    # 1 gold covers the remaining 1 emerald!
    action = {"type": "buy_card", "source": "board", "card_id": "c_test"}
    valid, msg = engine.validate_action(state, 0, action)
    assert valid is True

    new_state, event = engine.apply_action(state, 0, action)
    # Player spent 2 ruby and 1 gold
    assert new_state["players"][0]["tokens"]["ruby"] == 0
    assert new_state["players"][0]["tokens"]["gold"] == 0
    # Player gained sapphire bonus and 1 point
    assert new_state["players"][0]["bonuses"]["sapphire"] == 1
    assert new_state["players"][0]["prestige_points"] == 1
    assert len(new_state["players"][0]["cards"]) == 1

def test_noble_visit(engine, initial_state):
    state = initial_state
    noble = state["nobles"][0]
    # Set player bonuses to meet noble requirement
    for g, req in noble["requires"].items():
        state["players"][0]["bonuses"][g] = req

    # Let player 0 buy any cheap card to trigger noble visit check
    cheap_card = {"id": "c_cheap", "level": 1, "gem": "ruby", "points": 0, "cost": {}}
    state["board"]["1"][0] = cheap_card

    new_state, event = engine.apply_action(state, 0, {"type": "buy_card", "source": "board", "card_id": "c_cheap"})
    assert "noble_visited" in event
    assert len(new_state["players"][0]["nobles"]) == 1
    # Noble gives 3 points
    assert new_state["players"][0]["prestige_points"] == 3
    # Noble removed from board
    assert len(new_state["nobles"]) == 2

def test_final_round_and_tie_breaker(engine, initial_state):
    state = initial_state
    # Player 0 reaches 15 points
    high_card = {"id": "c_win", "level": 3, "gem": "diamond", "points": 15, "cost": {}}
    state["board"]["3"][0] = high_card

    state, event = engine.apply_action(state, 0, {"type": "buy_card", "source": "board", "card_id": "c_win"})
    assert state["final_round_triggered"] is True
    # Not game over yet! Player 1 must have equal turns (round completion)
    assert state["status"] == "playing"
    assert state["current_player"] == 1

    # Player 1 plays their final turn, also reaches 15 points but with 3 cards
    p1_card = {"id": "c_p1_win", "level": 3, "gem": "ruby", "points": 15, "cost": {}}
    state["board"]["3"][1] = p1_card
    state["players"][1]["cards"] = [
        {"id": "dummy1"}, {"id": "dummy2"}
    ]

    state, event = engine.apply_action(state, 1, {"type": "buy_card", "source": "board", "card_id": "c_p1_win"})
    # Now end of round 1 -> game over
    assert state["status"] == "finished"
    assert event["game_over"] is True
    # Player 0 has 1 card, Player 1 has 3 cards -> Player 0 wins tie-breaker!
    assert state["winner"]["player_index"] == 0
    assert state["winner"]["cards_count"] == 1
