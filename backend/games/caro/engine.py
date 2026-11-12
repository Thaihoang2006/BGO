import copy
from typing import Dict, Any, Tuple, Optional, List
from backend.games.base import BaseGameEngine

DEFAULT_BOARD_SIZE = 15
BOARD_SIZE = DEFAULT_BOARD_SIZE
EXPAND_MARGIN = 1  # Expand when a stone is placed on the border edge
EXPAND_STEP = 3    # Expand by 3 cells in that direction

class CaroEngine(BaseGameEngine):
    """Freestyle Gomoku (Caro) with dynamic expanding board.
    Starts at 15x15, expands outward whenever a piece is placed near any border.
    Strict server-authoritative rule verification.
    """

    def create_initial_state(self, players: List[Dict[str, Any]]) -> Dict[str, Any]:
        if len(players) != 2:
            raise ValueError("Caro requires exactly 2 players")

        rows = DEFAULT_BOARD_SIZE
        cols = DEFAULT_BOARD_SIZE
        grid = [[None for _ in range(cols)] for _ in range(rows)]

        return {
            "game_type": "caro",
            "board_size": rows,
            "rows": rows,
            "cols": cols,
            "grid": grid,
            "current_player": 0, # Player index 0 starts first ('X')
            "status": "playing", # 'playing', 'finished'
            "winner": None,      # None or dict {player_index, symbol, name, win_reason, winning_line}
            "moves_count": 0,
            "last_move": None,   # {row, col, player_index, symbol}
            "history": [],       # list of move records
            "players": [
                {
                    "player_index": p["player_index"],
                    "name": p.get("name", f"Player {p['player_index'] + 1}"),
                    "symbol": "X" if p["player_index"] == 0 else "O",
                    "color": p.get("color", "#FF9966" if p["player_index"] == 0 else "#FFE1BA")
                }
                for p in players
            ]
        }

    def validate_action(self, state: Dict[str, Any], player_index: int, action: Dict[str, Any]) -> Tuple[bool, str]:
        if state.get("status") != "playing":
            return False, "Trận đấu đã kết thúc"

        if state.get("current_player") != player_index:
            return False, "Chưa đến lượt của bạn"

        action_type = action.get("type")
        if action_type != "place_piece":
            return False, f"Hành động không hợp lệ: {action_type}"

        row = action.get("row")
        col = action.get("col")

        if row is None or col is None:
            return False, "Thiếu tọa độ nước đi (row, col)"

        if not isinstance(row, int) or not isinstance(col, int):
            return False, "Tọa độ nước đi phải là số nguyên"

        rows = state.get("rows", state.get("board_size", DEFAULT_BOARD_SIZE))
        cols = state.get("cols", state.get("board_size", DEFAULT_BOARD_SIZE))

        if row < 0 or row >= rows or col < 0 or col >= cols:
            return False, f"Tọa độ ({row}, {col}) nằm ngoài bàn cờ ({rows}x{cols})"

        grid = state.get("grid", [])
        if grid[row][col] is not None:
            return False, f"Ô ({row}, {col}) đã có quân"

        return True, ""

    def apply_action(self, state: Dict[str, Any], player_index: int, action: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        new_state = copy.deepcopy(state)
        row = action["row"]
        col = action["col"]
        symbol = "X" if player_index == 0 else "O"

        rows = new_state.get("rows", new_state.get("board_size", DEFAULT_BOARD_SIZE))
        cols = new_state.get("cols", new_state.get("board_size", DEFAULT_BOARD_SIZE))
        old_grid = new_state["grid"]

        # Check edge proximity for dynamic expansion
        pad_top = EXPAND_STEP if row < EXPAND_MARGIN else 0
        pad_bottom = EXPAND_STEP if row >= rows - EXPAND_MARGIN else 0
        pad_left = EXPAND_STEP if col < EXPAND_MARGIN else 0
        pad_right = EXPAND_STEP if col >= cols - EXPAND_MARGIN else 0

        board_expanded = (pad_top > 0 or pad_bottom > 0 or pad_left > 0 or pad_right > 0)

        if board_expanded:
            new_rows = rows + pad_top + pad_bottom
            new_cols = cols + pad_left + pad_right
            new_grid = [[None for _ in range(new_cols)] for _ in range(new_rows)]

            # Copy existing stones with padding offset
            for r in range(rows):
                for c in range(cols):
                    if old_grid[r][c] is not None:
                        new_grid[r + pad_top][c + pad_left] = old_grid[r][c]

            actual_row = row + pad_top
            actual_col = col + pad_left

            # Shift existing move coordinates in history
            for m in new_state.get("history", []):
                m["row"] += pad_top
                m["col"] += pad_left

            new_state["rows"] = new_rows
            new_state["cols"] = new_cols
            new_state["board_size"] = max(new_rows, new_cols)
            new_state["grid"] = new_grid
        else:
            new_rows = rows
            new_cols = cols
            actual_row = row
            actual_col = col

        # Place the new piece
        new_state["grid"][actual_row][actual_col] = symbol
        new_state["moves_count"] += 1

        last_move = {
            "row": actual_row,
            "col": actual_col,
            "player_index": player_index,
            "symbol": symbol,
            "move_number": new_state["moves_count"]
        }
        new_state["last_move"] = last_move
        new_state["history"].append(last_move)

        # Check win condition from actual placement
        winning_line = self._check_win(new_state["grid"], actual_row, actual_col, symbol, new_rows, new_cols)
        event_data = {
            "type": "piece_placed",
            "move": last_move,
            "board_expanded": board_expanded,
            "pad_top": pad_top,
            "pad_bottom": pad_bottom,
            "pad_left": pad_left,
            "pad_right": pad_right,
            "rows": new_rows,
            "cols": new_cols
        }

        if winning_line:
            player_info = next((p for p in new_state["players"] if p["player_index"] == player_index), {})
            winner_info = {
                "player_index": player_index,
                "symbol": symbol,
                "name": player_info.get("name", f"Player {player_index + 1}"),
                "win_reason": "five_in_a_row",
                "winning_line": winning_line
            }
            new_state["status"] = "finished"
            new_state["winner"] = winner_info
            event_data["game_over"] = True
            event_data["winner"] = winner_info
        else:
            # Switch turn to next player (0 -> 1 -> 0)
            new_state["current_player"] = 1 if player_index == 0 else 0
            event_data["next_player"] = new_state["current_player"]

        return new_state, event_data

    def _check_win(self, grid: List[List[Optional[str]]], r: int, c: int, symbol: str, rows: int, cols: int) -> Optional[List[List[int]]]:
        """Check 4 directions: Horizontal (-), Vertical (|), Diagonal (\\), Anti-Diagonal (/).
        Returns coordinates of the winning streak if >= 5 in a row, else None.
        """
        directions = [
            (0, 1),   # Horizontal
            (1, 0),   # Vertical
            (1, 1),   # Diagonal (\)
            (1, -1)   # Anti-diagonal (/)
        ]

        for dr, dc in directions:
            line = [[r, c]]

            # Forward check
            nr, nc = r + dr, c + dc
            while 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == symbol:
                line.append([nr, nc])
                nr += dr
                nc += dc

            # Backward check
            nr, nc = r - dr, c - dc
            while 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == symbol:
                line.append([nr, nc])
                nr -= dr
                nc -= dc

            if len(line) >= 5:
                line.sort(key=lambda pt: (pt[0], pt[1]))
                return line

        return None

    def get_public_state(self, state: Dict[str, Any], viewer_player_index: Optional[int] = None) -> Dict[str, Any]:
        return copy.deepcopy(state)
