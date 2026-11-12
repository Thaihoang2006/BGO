import pytest
from backend.games.caro.engine import CaroEngine, BOARD_SIZE

@pytest.fixture
def engine():
    return CaroEngine()

@pytest.fixture
def initial_state(engine):
    players = [
        {"player_index": 0, "name": "Alice", "color": "#FF9966"},
        {"player_index": 1, "name": "Bob", "color": "#FFE1BA"}
    ]
    return engine.create_initial_state(players)

def test_initial_state(initial_state):
    assert initial_state["game_type"] == "caro"
    assert initial_state["board_size"] == 15
    assert len(initial_state["grid"]) == 15
    assert len(initial_state["grid"][0]) == 15
    assert initial_state["current_player"] == 0
    assert initial_state["status"] == "playing"
    assert initial_state["winner"] is None
    assert initial_state["moves_count"] == 0
    assert initial_state["last_move"] is None

def test_turn_alternation(engine, initial_state):
    # Player 0 places at (7, 7)
    valid, msg = engine.validate_action(initial_state, 0, {"type": "place_piece", "row": 7, "col": 7})
    assert valid is True
    assert msg == ""

    state1, event1 = engine.apply_action(initial_state, 0, {"type": "place_piece", "row": 7, "col": 7})
    assert state1["grid"][7][7] == "X"
    assert state1["current_player"] == 1
    assert state1["moves_count"] == 1
    assert state1["last_move"]["row"] == 7
    assert state1["last_move"]["col"] == 7

    # Player 0 attempts to play again out of turn -> rejected
    valid, msg = engine.validate_action(state1, 0, {"type": "place_piece", "row": 7, "col": 8})
    assert valid is False
    assert "lượt" in msg.lower()

    # Player 1 places at (7, 8)
    valid, msg = engine.validate_action(state1, 1, {"type": "place_piece", "row": 7, "col": 8})
    assert valid is True
    state2, event2 = engine.apply_action(state1, 1, {"type": "place_piece", "row": 7, "col": 8})
    assert state2["grid"][7][8] == "O"
    assert state2["current_player"] == 0

def test_invalid_moves(engine, initial_state):
    # Out of bounds
    valid, _ = engine.validate_action(initial_state, 0, {"type": "place_piece", "row": -1, "col": 5})
    assert valid is False
    valid, _ = engine.validate_action(initial_state, 0, {"type": "place_piece", "row": 15, "col": 5})
    assert valid is False

    # Occupied cell
    state1, _ = engine.apply_action(initial_state, 0, {"type": "place_piece", "row": 7, "col": 7})
    valid, msg = engine.validate_action(state1, 1, {"type": "place_piece", "row": 7, "col": 7})
    assert valid is False
    assert "đã có quân" in msg.lower()

def test_horizontal_win(engine, initial_state):
    # Player 0 places 5 in a row: (7, 3), (7, 4), (7, 5), (7, 6), (7, 7)
    # Player 1 plays dummy moves at row 8
    state = initial_state
    moves_p0 = [(7, 3), (7, 4), (7, 5), (7, 6), (7, 7)]
    moves_p1 = [(8, 3), (8, 4), (8, 5), (8, 6)]

    for i in range(4):
        state, _ = engine.apply_action(state, 0, {"type": "place_piece", "row": moves_p0[i][0], "col": moves_p0[i][1]})
        assert state["status"] == "playing"
        state, _ = engine.apply_action(state, 1, {"type": "place_piece", "row": moves_p1[i][0], "col": moves_p1[i][1]})
        assert state["status"] == "playing"

    # Winning move for Player 0
    state, event = engine.apply_action(state, 0, {"type": "place_piece", "row": moves_p0[4][0], "col": moves_p0[4][1]})
    assert state["status"] == "finished"
    assert state["winner"]["player_index"] == 0
    assert state["winner"]["symbol"] == "X"
    assert len(state["winner"]["winning_line"]) == 5
    assert event.get("game_over") is True

    # No further moves allowed
    valid, msg = engine.validate_action(state, 1, {"type": "place_piece", "row": 8, "col": 7})
    assert valid is False
    assert "kết thúc" in msg.lower()

def test_diagonal_win(engine, initial_state):
    # Player 0 places diagonal: (2,2), (3,3), (4,4), (5,5), (6,6)
    state = initial_state
    for i in range(4):
        state, _ = engine.apply_action(state, 0, {"type": "place_piece", "row": 2 + i, "col": 2 + i})
        state, _ = engine.apply_action(state, 1, {"type": "place_piece", "row": 1, "col": i + 5})

    state, _ = engine.apply_action(state, 0, {"type": "place_piece", "row": 6, "col": 6})
    assert state["status"] == "finished"
    assert state["winner"]["player_index"] == 0
    assert len(state["winner"]["winning_line"]) == 5

def test_anti_diagonal_win(engine, initial_state):
    # Player 1 places anti-diagonal: (1, 5), (2, 4), (3, 3), (4, 2), (5, 1)
    state = initial_state
    p0_dummies = [(10, 1), (10, 2), (10, 3), (10, 4), (10, 5)]
    p1_moves = [(1, 5), (2, 4), (3, 3), (4, 2), (5, 1)]

    for i in range(4):
        state, _ = engine.apply_action(state, 0, {"type": "place_piece", "row": p0_dummies[i][0], "col": p0_dummies[i][1]})
        state, _ = engine.apply_action(state, 1, {"type": "place_piece", "row": p1_moves[i][0], "col": p1_moves[i][1]})
        assert state["status"] == "playing"

    state, _ = engine.apply_action(state, 0, {"type": "place_piece", "row": p0_dummies[4][0], "col": p0_dummies[4][1]})
    state, _ = engine.apply_action(state, 1, {"type": "place_piece", "row": p1_moves[4][0], "col": p1_moves[4][1]})

    assert state["status"] == "finished"
    assert state["winner"]["player_index"] == 1
    assert state["winner"]["symbol"] == "O"
    assert len(state["winner"]["winning_line"]) == 5

def test_dynamic_board_expansion(engine, initial_state):
    # Initial size 15x15
    state = initial_state
    assert state["rows"] == 15
    assert state["cols"] == 15

    # Place piece on top border (row 0)
    state, event = engine.apply_action(state, 0, {"type": "place_piece", "row": 0, "col": 7})
    assert event["board_expanded"] is True
    assert event["pad_top"] == 3
    # Rows should now be 18
    assert state["rows"] == 18
    assert state["cols"] == 15
    # The piece is placed at (0 + 3, 7) = (3, 7)
    assert state["grid"][3][7] == "X"

    # Next player places on right border: col = 14 (cols - 1)
    state, event = engine.apply_action(state, 1, {"type": "place_piece", "row": 5, "col": 14})
    assert event["board_expanded"] is True
    assert event["pad_right"] == 3
    # Cols should now be 18
    assert state["cols"] == 18
    assert state["rows"] == 18
