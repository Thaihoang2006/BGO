import copy
import random
from typing import Dict, Any, Tuple, Optional, List
from backend.games.base import BaseGameEngine

BOARD_TILES = [
    {"id": 0, "name": "Khởi Hành (GO)", "type": "go", "color": "#795463"},
    {"id": 1, "name": "Hà Giang", "type": "property", "color": "#8d5b4c", "price": 80, "base_rent": 15, "house_cost": 50},
    {"id": 2, "name": "Cơ Hội", "type": "chance", "color": "#BE807D"},
    {"id": 3, "name": "Sa Pa", "type": "property", "color": "#8d5b4c", "price": 100, "base_rent": 20, "house_cost": 50},
    {"id": 4, "name": "Thuế Đô Thị", "type": "tax", "color": "#795463", "amount": 100},
    {"id": 5, "name": "Ga Hà Nội", "type": "station", "color": "#6c757d", "price": 150, "base_rent": 35},
    {"id": 6, "name": "Hạ Long", "type": "property", "color": "#48cae4", "price": 120, "base_rent": 25, "house_cost": 60},
    {"id": 7, "name": "Nhà Tù", "type": "jail", "color": "#251620"},
    {"id": 8, "name": "Hải Phòng", "type": "property", "color": "#48cae4", "price": 140, "base_rent": 30, "house_cost": 60},
    {"id": 9, "name": "Khí Vận", "type": "chest", "color": "#BE807D"},
    {"id": 10, "name": "Huế", "type": "property", "color": "#b5179e", "price": 160, "base_rent": 35, "house_cost": 80},
    {"id": 11, "name": "Đà Nẵng", "type": "property", "color": "#b5179e", "price": 180, "base_rent": 40, "house_cost": 80},
    {"id": 12, "name": "Bãi Đỗ Xe", "type": "parking", "color": "#795463"},
    {"id": 13, "name": "Hội An", "type": "property", "color": "#f77f00", "price": 200, "base_rent": 45, "house_cost": 100},
    {"id": 14, "name": "Cơ Hội", "type": "chance", "color": "#BE807D"},
    {"id": 15, "name": "Nha Trang", "type": "property", "color": "#f77f00", "price": 220, "base_rent": 50, "house_cost": 100},
    {"id": 16, "name": "Sân Bay", "type": "station", "color": "#6c757d", "price": 150, "base_rent": 35},
    {"id": 17, "name": "Đà Lạt", "type": "property", "color": "#e9d8a6", "price": 240, "base_rent": 55, "house_cost": 120},
    {"id": 18, "name": "Vào Tù!", "type": "go_to_jail", "color": "#d90429"},
    {"id": 19, "name": "Vũng Tàu", "type": "property", "color": "#e9d8a6", "price": 260, "base_rent": 60, "house_cost": 120},
    {"id": 20, "name": "Cần Thơ", "type": "property", "color": "#2a9d8f", "price": 280, "base_rent": 65, "house_cost": 140},
    {"id": 21, "name": "Khí Vận", "type": "chest", "color": "#BE807D"},
    {"id": 22, "name": "Phú Quốc", "type": "property", "color": "#2a9d8f", "price": 300, "base_rent": 70, "house_cost": 140},
    {"id": 23, "name": "Sài Gòn", "type": "property", "color": "#023e8a", "price": 350, "base_rent": 85, "house_cost": 160}
]

CHANCE_CARDS = [
    {"text": "Trúng giải thưởng kiến thiết! Nhận $100", "amount": 100},
    {"text": "Được thưởng hiệu suất làm việc! Nhận $150", "amount": 150},
    {"text": "Sửa chữa xe hơi và bảo hiểm. Trả $50", "amount": -50},
    {"text": "Đãi tiệc bạn bè cuối tuần. Trả $80", "amount": -80},
    {"text": "Đầu tư chứng khoán sinh lời! Nhận $200", "amount": 200}
]

DEFAULT_COLORS = ["#FF9966", "#3A86FF", "#06D6A0", "#FFBE0B"]

class MonopolyEngine(BaseGameEngine):
    """Vietnamese Property Tycoon (Cờ Tỷ Phú) Engine.
    Features 24-tile board, cash management, property deed purchasing,
    building houses for increased rent, tax, jail, chance cards, and bankruptcy.
    """

    def create_initial_state(self, players: List[Dict[str, Any]]) -> Dict[str, Any]:
        num = len(players)
        if num < 2 or num > 4:
            raise ValueError("Property Tycoon requires 2 to 4 players")

        player_states = [
            {
                "player_index": p["player_index"],
                "name": p.get("name", f"Player {p['player_index'] + 1}"),
                "color": p.get("color", DEFAULT_COLORS[i % len(DEFAULT_COLORS)]),
                "symbol": ["🚗", "🚢", "🎩", "🐎"][i % 4],
                "cash": 1500,
                "position": 0,
                "in_jail": False,
                "jail_turns": 0,
                "is_bankrupt": False,
                "properties": []  # List of tile ids
            }
            for i, p in enumerate(players)
        ]

        # Property registry: { tile_id: { owner: None, houses: 0 } }
        property_states = {}
        for t in BOARD_TILES:
            if t["type"] in ("property", "station"):
                property_states[str(t["id"])] = {
                    "owner": None,
                    "houses": 0
                }

        return {
            "game_type": "monopoly",
            "tiles": BOARD_TILES,
            "properties": property_states,
            "players": player_states,
            "current_player": 0,
            "status": "playing",           # 'playing', 'finished'
            "phase": "roll",               # 'roll', 'decision', 'turn_end'
            "dice": [1, 1],
            "last_dice_sum": 0,
            "can_build": False,
            "pending_tile": None,          # Tile player is currently on for buying
            "last_log": "Bắt đầu ván Cờ Tỷ Phú! Người chơi 1 hãy gieo xúc xắc.",
            "winner": None,
            "round_number": 1
        }

    def validate_action(self, state: Dict[str, Any], player_index: int, action: Dict[str, Any]) -> Tuple[bool, str]:
        if state.get("status") != "playing":
            return False, "Trận đấu đã kết thúc"

        if state.get("current_player") != player_index:
            return False, "Chưa đến lượt của bạn"

        curr_p = state["players"][player_index]
        if curr_p["is_bankrupt"]:
            return False, "Bạn đã phá sản"

        action_type = action.get("type")
        phase = state.get("phase", "roll")

        if action_type == "roll_dice":
            if phase != "roll":
                return False, "Bạn đã gieo xúc xắc lượt này rồi"
            return True, ""

        elif action_type == "buy_property":
            if phase != "decision":
                return False, "Không có bất động sản nào đang chờ mua"
            tile_id = state.get("pending_tile")
            if tile_id is None:
                return False, "Không có ô đất hợp lệ"
            tile = next((t for t in BOARD_TILES if t["id"] == tile_id), None)
            if not tile or tile["type"] not in ("property", "station"):
                return False, "Ô này không phải bất động sản"
            prop_state = state["properties"].get(str(tile_id))
            if prop_state and prop_state["owner"] is not None:
                return False, "Khu đất này đã có chủ sở hữu"
            if curr_p["cash"] < tile["price"]:
                return False, f"Không đủ tiền để mua đất (cần ${tile['price']}, bạn có ${curr_p['cash']})"
            return True, ""

        elif action_type == "pass_buy":
            if phase != "decision":
                return False, "Hiện không có lựa chọn mua đất nào"
            return True, ""

        elif action_type == "build_house":
            tile_id = action.get("tile_id")
            if tile_id is None:
                return False, "Vui lòng chọn ô đất để xây nhà"
            tile = next((t for t in BOARD_TILES if t["id"] == tile_id), None)
            if not tile or tile["type"] != "property":
                return False, "Chỉ có thể xây nhà trên ô đất thành phố"
            prop_state = state["properties"].get(str(tile_id))
            if not prop_state or prop_state["owner"] != player_index:
                return False, "Bạn không sở hữu mảnh đất này"
            if prop_state["houses"] >= 3:
                return False, "Mảnh đất này đã xây tối đa 3 ngôi nhà"
            house_cost = tile.get("house_cost", 50)
            if curr_p["cash"] < house_cost:
                return False, f"Không đủ tiền xây nhà (cần ${house_cost})"
            return True, ""

        elif action_type == "pay_jail_fine":
            if not curr_p["in_jail"]:
                return False, "Bạn không ở trong tù"
            if curr_p["cash"] < 50:
                return False, "Không đủ $50 để đóng tiền phạt ra tù"
            return True, ""

        elif action_type == "end_turn":
            if phase == "roll":
                return False, "Vui lòng gieo xúc xắc trước khi kết thúc lượt"
            return True, ""

        return False, f"Hành động không hợp lệ: {action_type}"

    def apply_action(self, state: Dict[str, Any], player_index: int, action: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        new_state = copy.deepcopy(state)
        action_type = action["type"]
        curr_p = new_state["players"][player_index]

        if action_type == "pay_jail_fine":
            curr_p["cash"] -= 50
            curr_p["in_jail"] = False
            curr_p["jail_turns"] = 0
            new_state["last_log"] = f"{curr_p['name']} đã trả $50 bảo lãnh ra khỏi tù!"
            return new_state, {"type": "jail_fine_paid"}

        elif action_type == "roll_dice":
            d1 = random.randint(1, 6)
            d2 = random.randint(1, 6)
            dice_sum = d1 + d2
            new_state["dice"] = [d1, d2]
            new_state["last_dice_sum"] = dice_sum

            # Check jail status
            if curr_p["in_jail"]:
                if d1 == d2:
                    curr_p["in_jail"] = False
                    curr_p["jail_turns"] = 0
                    new_state["last_log"] = f"🎉 {curr_p['name']} đổ đôi {d1}-{d2}! Thoát khỏi nhà tù thành công."
                else:
                    curr_p["jail_turns"] += 1
                    if curr_p["jail_turns"] >= 3:
                        # Must pay $50 after 3 failed attempts
                        curr_p["cash"] -= 50
                        curr_p["in_jail"] = False
                        curr_p["jail_turns"] = 0
                        new_state["last_log"] = f"{curr_p['name']} đã bị giữ 3 lượt, tự động trả $50 và ra tù."
                    else:
                        new_state["phase"] = "turn_end"
                        new_state["last_log"] = f"{curr_p['name']} đổ {d1}-{d2} (không đôi). Vẫn phải ở trong tù."
                        return new_state, {"type": "dice_rolled", "dice": [d1, d2]}

            # Advance player
            old_pos = curr_p["position"]
            new_pos = (old_pos + dice_sum) % len(BOARD_TILES)
            curr_p["position"] = new_pos

            # Passed GO bonus?
            passed_go = new_pos < old_pos
            if passed_go:
                curr_p["cash"] += 200
                new_state["last_log"] = f"{curr_p['name']} vượt qua vạch Khởi Hành nhận thưởng $200! "
            else:
                new_state["last_log"] = ""

            tile = BOARD_TILES[new_pos]
            tile_type = tile["type"]
            new_state["last_log"] += f"🎲 {curr_p['name']} đổ được {dice_sum} ({d1}+{d2}), tiến vào ô {tile['name']}."

            # Process landing on tile
            if tile_type in ("property", "station"):
                prop_key = str(tile["id"])
                prop = new_state["properties"][prop_key]
                if prop["owner"] is None:
                    # Can buy
                    new_state["phase"] = "decision"
                    new_state["pending_tile"] = tile["id"]
                    new_state["last_log"] += f" Khu đất chưa có chủ, giá mua ${tile['price']}."
                elif prop["owner"] != player_index:
                    # Must pay rent
                    owner = new_state["players"][prop["owner"]]
                    if not owner["is_bankrupt"]:
                        # Calculate rent: base_rent * (1 + houses * 0.7)
                        houses = prop.get("houses", 0)
                        rent = int(tile["base_rent"] * (1 + houses * 0.7))
                        curr_p["cash"] -= rent
                        owner["cash"] += rent
                        new_state["last_log"] += f" Đã trả ${rent} tiền thuê đất cho {owner['name']}."
                    new_state["phase"] = "turn_end"
                else:
                    # Landed on own property
                    new_state["phase"] = "turn_end"

            elif tile_type == "go_to_jail":
                curr_p["position"] = 7
                curr_p["in_jail"] = True
                curr_p["jail_turns"] = 0
                new_state["phase"] = "turn_end"
                new_state["last_log"] += " 🚨 Bạn đã bị bắt vào Nhà Tù!"

            elif tile_type == "tax":
                tax_amt = tile.get("amount", 100)
                curr_p["cash"] -= tax_amt
                new_state["phase"] = "turn_end"
                new_state["last_log"] += f" Đã đóng ${tax_amt} tiền thuế cho ngân khố."

            elif tile_type in ("chance", "chest"):
                card = random.choice(CHANCE_CARDS)
                curr_p["cash"] += card["amount"]
                new_state["phase"] = "turn_end"
                new_state["last_log"] += f" 📜 Rút thẻ sự kiện: {card['text']}"

            else:
                new_state["phase"] = "turn_end"

            # Check if player went bankrupt
            if curr_p["cash"] < 0:
                self._handle_bankruptcy(new_state, player_index)

            # Check win condition
            self._check_game_over(new_state)

            return new_state, {
                "type": "dice_rolled",
                "dice": [d1, d2],
                "position": new_pos,
                "passed_go": passed_go
            }

        elif action_type == "buy_property":
            tile_id = new_state["pending_tile"]
            tile = next((t for t in BOARD_TILES if t["id"] == tile_id), None)
            curr_p["cash"] -= tile["price"]
            curr_p["properties"].append(tile_id)
            new_state["properties"][str(tile_id)]["owner"] = player_index
            new_state["pending_tile"] = None
            new_state["phase"] = "turn_end"
            new_state["last_log"] = f"🏠 {curr_p['name']} đã mua khu đất {tile['name']} với giá ${tile['price']}!"
            return new_state, {"type": "property_bought", "tile_id": tile_id}

        elif action_type == "pass_buy":
            new_state["pending_tile"] = None
            new_state["phase"] = "turn_end"
            new_state["last_log"] = f"{curr_p['name']} quyết định không mua khu đất này."
            return new_state, {"type": "property_buy_passed"}

        elif action_type == "build_house":
            tile_id = action["tile_id"]
            tile = next((t for t in BOARD_TILES if t["id"] == tile_id), None)
            cost = tile.get("house_cost", 50)
            curr_p["cash"] -= cost
            new_state["properties"][str(tile_id)]["houses"] += 1
            h_count = new_state["properties"][str(tile_id)]["houses"]
            new_state["last_log"] = f"🔨 {curr_p['name']} đã chi ${cost} xây thêm ngôi nhà thứ {h_count} tại {tile['name']}!"
            return new_state, {"type": "house_built", "tile_id": tile_id, "houses": h_count}

        elif action_type == "end_turn":
            # Switch to next non-bankrupt player
            active_players = [p for p in new_state["players"] if not p["is_bankrupt"]]
            if len(active_players) <= 1:
                self._check_game_over(new_state)
                return new_state, {"type": "turn_ended"}

            next_idx = player_index
            for _ in range(len(new_state["players"])):
                next_idx = (next_idx + 1) % len(new_state["players"])
                if not new_state["players"][next_idx]["is_bankrupt"]:
                    break

            new_state["current_player"] = next_idx
            new_state["phase"] = "roll"
            new_state["pending_tile"] = None
            next_name = new_state["players"][next_idx]["name"]
            new_state["last_log"] = f"Chuyển lượt sang {next_name}. Hãy gieo xúc xắc!"

            return new_state, {"type": "turn_ended", "next_player": next_idx}

        return new_state, {}

    def _handle_bankruptcy(self, state: Dict[str, Any], player_index: int):
        player = state["players"][player_index]
        player["is_bankrupt"] = True
        player["cash"] = 0
        # Release all owned properties back to bank
        for p_id in player["properties"]:
            state["properties"][str(p_id)]["owner"] = None
            state["properties"][str(p_id)]["houses"] = 0
        player["properties"] = []
        state["last_log"] += f" 💥 {player['name']} đã hết tiền và bị PHÁ SẢN!"

    def _check_game_over(self, state: Dict[str, Any]):
        active_players = [p for p in state["players"] if not p["is_bankrupt"]]
        if len(active_players) == 1:
            winner = active_players[0]
            winner_info = {
                "player_index": winner["player_index"],
                "name": winner["name"],
                "color": winner["color"],
                "symbol": winner["symbol"],
                "win_reason": "sole_survivor"
            }
            state["status"] = "finished"
            state["winner"] = winner_info

    def get_public_state(self, state: Dict[str, Any], viewer_player_index: Optional[int] = None) -> Dict[str, Any]:
        return copy.deepcopy(state)
