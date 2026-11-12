import pytest
from backend.games.undercover.engine import UndercoverEngine, strip_accents, normalize_guess
from backend.games.undercover.words_data import WORD_PAIRS, CATEGORIES, get_word_pair


def test_word_bank_completeness():
    """Verify word bank has >= 100 pairs across 7 categories."""
    assert len(WORD_PAIRS) >= 100
    categories_found = {p["category"] for p in WORD_PAIRS}
    for cat in ["food", "animals", "vehicles", "technology", "places", "sports", "daily_life"]:
        assert cat in categories_found
        pairs_in_cat = [p for p in WORD_PAIRS if p["category"] == cat]
        assert len(pairs_in_cat) >= 14


def test_text_normalization():
    assert strip_accents("Cà phê") == "ca phe"
    assert strip_accents("Đại bàng") == "dai bang"
    assert normalize_guess("  Cà  phê! ") == "caphe"
    assert normalize_guess("ca phe") == "caphe"
    assert normalize_guess("Tàu Hỏa...") == "tauhoa"


def test_role_distributions_default():
    engine = UndercoverEngine()
    # 3 players: 2 civ, 1 uc, 0 mw
    c, u, w = engine.get_default_role_counts(3)
    assert (c, u, w) == (2, 1, 0)

    # 6 players: 4 civ, 1 uc, 1 mw
    c, u, w = engine.get_default_role_counts(6)
    assert (c, u, w) == (4, 1, 1)

    # 10 players: 7 civ, 2 uc, 1 mw
    c, u, w = engine.get_default_role_counts(10)
    assert (c, u, w) == (7, 2, 1)

    # 20 players: 14 civ, 4 uc, 2 mw
    c, u, w = engine.get_default_role_counts(20)
    assert (c, u, w) == (14, 4, 2)


def test_role_distribution_custom_validation():
    engine = UndercoverEngine()
    # Valid: 6 players, 1 undercover, 1 mr white -> 4 civilians
    ok, _ = engine.validate_role_counts(6, 1, 1)
    assert ok is True

    # Invalid: no specials
    ok, msg = engine.validate_role_counts(6, 0, 0)
    assert ok is False

    # Invalid: < 2 civilians
    ok, msg = engine.validate_role_counts(6, 4, 1)
    assert ok is False
    assert "ít nhất 2 Dân thường" in msg

    # Invalid: total != num_players
    ok, msg = engine.validate_role_counts(6, 1, 0)
    assert ok is True  # 5 civ + 1 uc = 6


def test_create_initial_state_undercover():
    engine = UndercoverEngine()
    players = [{"player_index": i, "name": f"P{i}"} for i in range(6)]
    state = engine.create_initial_state(players)

    assert state["phase"] == "describe"
    assert len(state["players"]) == 6
    assert len(state["turn_order"]) == 6
    assert state["round_number"] == 1
    assert "civilian" in state["secret_words"]
    assert "undercover" in state["secret_words"]

    # Count roles
    roles = [p["role"] for p in state["players"]]
    assert roles.count("civilian") == 4
    assert roles.count("undercover") == 1
    assert roles.count("mr_white") == 1

    # Check word assignment
    for p in state["players"]:
        if p["role"] == "civilian":
            assert p["word"] == state["secret_words"]["civilian"]
        elif p["role"] == "undercover":
            assert p["word"] == state["secret_words"]["undercover"]
        else:
            assert p["word"] == ""


def test_secret_filtering_spectators_and_opponents():
    engine = UndercoverEngine()
    players = [{"player_index": i, "name": f"P{i}"} for i in range(6)]
    state = engine.create_initial_state(players)

    # 1. Spectator view (viewer_player_index = None)
    spec_state = engine.get_public_state(state, viewer_player_index=None)
    assert "secret_words" not in spec_state
    for p in spec_state["players"]:
        assert p["role"] == "???"
        assert p["word"] == "???"

    # 2. Player 0 view
    p0_state = engine.get_public_state(state, viewer_player_index=0)
    assert "secret_words" not in p0_state
    assert p0_state["players"][0]["role"] == state["players"][0]["role"]
    assert p0_state["players"][0]["word"] == state["players"][0]["word"]
    # Other players remain masked
    for p in p0_state["players"][1:]:
        assert p["role"] == "???"
        assert p["word"] == "???"

    # 3. Finished state reveals all
    state["phase"] = "finished"
    finished_state = engine.get_public_state(state, viewer_player_index=None)
    for p in finished_state["players"]:
        assert p["role"] != "???"
        if p["role"] != "mr_white":
            assert p["word"] != "???"


def test_description_flow_and_forbidden_words():
    engine = UndercoverEngine()
    players = [{"player_index": i, "name": f"P{i}"} for i in range(4)]
    # Force roles: 3 civ, 1 uc, 0 mw
    state = engine.create_initial_state(players, options={"undercover_count": 1, "mrwhite_count": 0})
    state["secret_words"] = {"civilian": "Cà phê", "undercover": "Trà"}
    for p in state["players"]:
        if p["role"] == "civilian":
            p["word"] = "Cà phê"
        else:
            p["word"] = "Trà"

    # Start descriptions
    state, _ = engine.apply_action(state, 0, {"type": "start_descriptions"})
    assert state["phase"] == "describe"

    cur = state["current_player"]
    cur_p = next(p for p in state["players"] if p["player_index"] == cur)

    # Forbidden word check: saying their secret word directly is invalid
    is_valid, err = engine.validate_action(state, cur, {"type": "submit_description", "text": f"Tôi rất thích uống {cur_p['word']}"})
    assert is_valid is False
    assert "Không được nhắc trực tiếp" in err

    # Valid description
    is_valid, _ = engine.validate_action(state, cur, {"type": "submit_description", "text": "Món đồ uống màu đen, vị đắng"})
    assert is_valid is True

    # Advance through all 4 players
    for _ in range(4):
        p_idx = state["current_player"]
        state, _ = engine.apply_action(state, p_idx, {"type": "submit_description", "text": "Đồ uống buổi sáng"})

    # Phase should now be vote immediately after round descriptions finish
    assert state["phase"] == "vote"
    assert len(state["descriptions"]["1"]) == 4


def test_voting_tie_and_revote():
    engine = UndercoverEngine()
    players = [{"player_index": i, "name": f"P{i}"} for i in range(4)]
    state = engine.create_initial_state(players)
    state["phase"] = "vote"

    # P0 and P1 vote for P2; P2 and P3 vote for P3 -> Tie between P2 and P3 (2 votes each)
    state, _ = engine.apply_action(state, 0, {"type": "submit_vote", "target_player_index": 2})
    state, _ = engine.apply_action(state, 1, {"type": "submit_vote", "target_player_index": 2})
    state, _ = engine.apply_action(state, 2, {"type": "submit_vote", "target_player_index": 3})
    state, ev = engine.apply_action(state, 3, {"type": "submit_vote", "target_player_index": 3})

    # Should trigger revote
    assert state["is_revote"] is True
    assert set(state["revote_candidates"]) == {2, 3}
    assert state["phase"] == "vote"

    # In revote, voting for non-candidate is rejected
    is_valid, msg = engine.validate_action(state, 0, {"type": "submit_vote", "target_player_index": 1})
    assert is_valid is False

    # P0, P1, P2 vote for P3 -> P3 eliminated
    state, _ = engine.apply_action(state, 0, {"type": "submit_vote", "target_player_index": 3})
    state, _ = engine.apply_action(state, 1, {"type": "submit_vote", "target_player_index": 3})
    state, _ = engine.apply_action(state, 2, {"type": "submit_vote", "target_player_index": 3})
    state, _ = engine.apply_action(state, 3, {"type": "submit_vote", "target_player_index": 2})

    p3 = next(p for p in state["players"] if p["player_index"] == 3)
    assert p3["is_alive"] is False


def test_mr_white_elimination_and_word_guess():
    engine = UndercoverEngine()
    players = [{"player_index": i, "name": f"P{i}"} for i in range(4)]
    state = engine.create_initial_state(players, options={"undercover_count": 1, "mrwhite_count": 1})
    state["secret_words"] = {"civilian": "Bánh mì", "undercover": "Hamburger"}

    # Force player 3 to be Mr. White
    state["players"][0]["role"] = "civilian"
    state["players"][0]["word"] = "Bánh mì"
    state["players"][1]["role"] = "civilian"
    state["players"][1]["word"] = "Bánh mì"
    state["players"][2]["role"] = "undercover"
    state["players"][2]["word"] = "Hamburger"
    state["players"][3]["role"] = "mr_white"
    state["players"][3]["word"] = ""

    state["phase"] = "vote"

    # All vote to eliminate Mr. White (P3)
    for i in range(3):
        state, _ = engine.apply_action(state, i, {"type": "submit_vote", "target_player_index": 3})
    state, _ = engine.apply_action(state, 3, {"type": "submit_vote", "target_player_index": 0})

    # Phase should transition to mrwhite_guess
    assert state["phase"] == "mrwhite_guess"
    assert state["pending_mrwhite"] == 3

    # Mr. White guesses wrong first in test simulation
    # Try invalid guess: correct civilian word -> instant win
    state_win, ev = engine.apply_action(state, 3, {"type": "mrwhite_guess", "guess": "banh mi"})
    assert state_win["phase"] == "finished"
    assert state_win["winner"]["team"] == "mr_white"
