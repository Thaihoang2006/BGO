import copy
import random
from typing import Dict, Any, Tuple, Optional, List
from backend.games.base import BaseGameEngine

TRACK_LENGTH = 56  # 56 common step cells around the perimeter
HOME_TIERS = 6     # 6 home tiers (1 to 6)
START_STEPS = [0, 14, 28, 42] # Start steps for players 0, 1, 2, 3
DEFAULT_COLORS = ["#FF4838", "#78C800", "#FFBE0B", "#00BCD4"] # Red, Green, Yellow, Cyan

class LudoEngine(BaseGameEngine):
    """Vietnamese Ludo (Cờ Cá Ngựa) Engine.
    Supports 2 to 4 players, server-authoritative dice rolls,
    capturing/kicking opponent horses, home climbing tiers, and bonus turn on roll 6.
    """

    def create_initial_state(self, players: List[Dict[str, Any]]) -> Dict[str, Any]:
        num_players = len(players)
        if num_players < 2 or num_players > 4:
            raise ValueError("Ludo requires 2 to 4 players")

        player_states = []
        for i, p in enumerate(players):
            start_step = START_STEPS[i]
            home_entry = (start_step + TRACK_LENGTH - 1) % TRACK_LENGTH
            player_states.append({
                "player_index": p["player_index"],
                "name": p.get("name", f"Player {p['player_index'] + 1}"),
                "color": p.get("color", DEFAULT_COLORS[i % len(DEFAULT_COLORS)]),
                "symbol": f"H{i+1}",
                "start_step": start_step,
                "home_entry_step": home_entry,
                "horses": [
                    {
                        "id": h_id,
                        "status": "stable",   # 'stable', 'on_track', 'home', 'finished'
                        "step": 0,            # 0..55 when on track; 1..6 when in home
                        "distance_walked": 0  # Steps traveled from start
                    }
                    for h_id in range(4)
                ],
                "finished_count": 0
            })

        return {
            "game_type": "ludo",
            "players": player_states,
            "current_player": 0,
            "status": "playing",           # 'playing', 'finished'
            "phase": "roll",               # 'roll' or 'select_horse'
            "dice_value": None,
            "bonus_roll": False,
            "valid_horse_ids": [],
            "last_action_desc": "Bắt đầu ván cờ Cá Ngựa. Người chơi 1 hãy đổ xúc xắc!",
            "winner": None,
            "history": []
        }

    def validate_action(self, state: Dict[str, Any], player_index: int, action: Dict[str, Any]) -> Tuple[bool, str]:
        if state.get("status") != "playing":
            return False, "Trận đấu đã kết thúc"

        if state.get("current_player") != player_index:
            return False, "Chưa đến lượt của bạn"

        action_type = action.get("type")

        if action_type == "roll_dice":
            if state.get("phase") != "roll":
                return False, "Bạn đã đổ xúc xắc rồi, hãy chọn một quân cờ để di chuyển"
            return True, ""

        elif action_type == "move_horse":
            if state.get("phase") != "select_horse":
                return False, "Vui lòng đổ xúc xắc trước khi chọn quân"

            horse_id = action.get("horse_id")
            if horse_id is None or horse_id not in state.get("valid_horse_ids", []):
                return False, f"Quân ngựa #{horse_id} không thể di chuyển với số nút hiện tại"

            return True, ""

        return False, f"Hành động không hợp lệ: {action_type}"

    def apply_action(self, state: Dict[str, Any], player_index: int, action: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        new_state = copy.deepcopy(state)
        action_type = action["type"]
        curr_p = new_state["players"][player_index]

        if action_type == "roll_dice":
            # Roll D6
            dice = random.randint(1, 6)
            new_state["dice_value"] = dice
            new_state["bonus_roll"] = (dice == 6)

            # Calculate which horses can legally move with this dice value
            valid_horses = self._get_valid_horses(new_state, player_index, dice)
            new_state["valid_horse_ids"] = valid_horses

            if valid_horses:
                new_state["phase"] = "select_horse"
                new_state["last_action_desc"] = f"{curr_p['name']} đổ được {dice} điểm! Hãy chọn 1 chú ngựa để đi."
                event_data = {
                    "type": "dice_rolled",
                    "dice": dice,
                    "valid_horses": valid_horses,
                    "bonus_roll": new_state["bonus_roll"]
                }
            else:
                # No moves available
                if new_state["bonus_roll"]:
                    # Can roll again on 6 even if cannot move
                    new_state["phase"] = "roll"
                    new_state["last_action_desc"] = f"{curr_p['name']} đổ được 6 nhưng không có nước đi hợp lệ. Đổ lại lượt thưởng!"
                    event_data = {
                        "type": "dice_rolled_no_move",
                        "dice": dice,
                        "bonus_roll": True
                    }
                else:
                    # Pass turn to next player
                    next_p = (player_index + 1) % len(new_state["players"])
                    new_state["current_player"] = next_p
                    new_state["phase"] = "roll"
                    new_state["dice_value"] = dice
                    new_state["last_action_desc"] = f"{curr_p['name']} đổ được {dice} nhưng không có nước đi. Chuyển lượt sang {new_state['players'][next_p]['name']}."
                    event_data = {
                        "type": "turn_passed",
                        "dice": dice,
                        "next_player": next_p
                    }

            return new_state, event_data

        elif action_type == "move_horse":
            horse_id = action["horse_id"]
            dice = new_state["dice_value"]
            horse = curr_p["horses"][horse_id]

            kicked_info = None

            if horse["status"] == "stable":
                # Deploy horse out to start step
                horse["status"] = "on_track"
                horse["step"] = curr_p["start_step"]
                horse["distance_walked"] = 0

                # Check if an opponent horse is on the start gate -> KICK!
                kicked_info = self._check_kick(new_state, player_index, horse["step"])
                new_state["last_action_desc"] = f"🚀 {curr_p['name']} đã xuất quân ngựa #{horse_id + 1} ra trận!"

            elif horse["status"] == "on_track":
                # Advancing on track
                new_dist = horse["distance_walked"] + dice

                if new_dist >= TRACK_LENGTH:
                    # Entering home column tiers!
                    home_tier = new_dist - TRACK_LENGTH + 1
                    if home_tier <= HOME_TIERS:
                        horse["status"] = "home"
                        horse["step"] = home_tier
                        horse["distance_walked"] = new_dist
                        new_state["last_action_desc"] = f"🏁 {curr_p['name']} đưa ngựa #{horse_id + 1} vào chuồng đích bậc {home_tier}!"
                        if home_tier >= 5:
                            curr_p["finished_count"] += 1
                else:
                    # Normal track move
                    new_step = (horse["step"] + dice) % TRACK_LENGTH
                    horse["step"] = new_step
                    horse["distance_walked"] = new_dist

                    # Check for kick
                    kicked_info = self._check_kick(new_state, player_index, new_step)
                    new_state["last_action_desc"] = f"🐎 {curr_p['name']} di chuyển ngựa #{horse_id + 1} tiến {dice} ô!"

            elif horse["status"] == "home":
                # Climbing higher home tier
                target_tier = horse["step"] + dice
                if target_tier <= HOME_TIERS:
                    old_tier = horse["step"]
                    horse["step"] = target_tier
                    new_state["last_action_desc"] = f"⭐ {curr_p['name']} đưa ngựa #{horse_id + 1} leo lên bậc {target_tier}!"
                    if target_tier >= 5 and old_tier < 5:
                        curr_p["finished_count"] += 1

            if kicked_info:
                new_state["last_action_desc"] += f" 💥 Đã ĐÁ ngựa của {kicked_info['victim_name']} về chuồng!"

            # Check win condition: 2 horses in top home tiers (tier 5 or 6)
            if curr_p["finished_count"] >= 2:
                winner_info = {
                    "player_index": player_index,
                    "name": curr_p["name"],
                    "color": curr_p["color"],
                    "symbol": curr_p["symbol"],
                    "win_reason": "horses_home"
                }
                new_state["status"] = "finished"
                new_state["winner"] = winner_info
                event_data = {
                    "type": "game_over",
                    "winner": winner_info,
                    "kicked": kicked_info
                }
                return new_state, event_data

            # Check bonus turn on 6
            if new_state.get("bonus_roll"):
                new_state["phase"] = "roll"
                new_state["dice_value"] = None
                new_state["valid_horse_ids"] = []
                new_state["last_action_desc"] += f" Đổ được 6 nên {curr_p['name']} được đổ thêm lượt!"
                event_data = {
                    "type": "horse_moved",
                    "horse_id": horse_id,
                    "bonus_roll": True,
                    "kicked": kicked_info
                }
            else:
                next_p = (player_index + 1) % len(new_state["players"])
                new_state["current_player"] = next_p
                new_state["phase"] = "roll"
                new_state["dice_value"] = None
                new_state["valid_horse_ids"] = []
                event_data = {
                    "type": "horse_moved",
                    "horse_id": horse_id,
                    "next_player": next_p,
                    "kicked": kicked_info
                }

            return new_state, event_data

        return new_state, {}

    def _get_valid_horses(self, state: Dict[str, Any], player_index: int, dice: int) -> List[int]:
        player = state["players"][player_index]
        valid = []

        for h in player["horses"]:
            if h["status"] == "stable":
                # Can deploy if dice is 1 or 6 (traditional Vietnamese Ludo) and start gate not blocked by OWN horse
                if dice in (1, 6):
                    start_step = player["start_step"]
                    blocked_by_own = any(
                        other["status"] == "on_track" and other["step"] == start_step
                        for other in player["horses"]
                    )
                    if not blocked_by_own:
                        valid.append(h["id"])

            elif h["status"] == "on_track":
                new_dist = h["distance_walked"] + dice
                if new_dist >= TRACK_LENGTH:
                    tier = new_dist - TRACK_LENGTH + 1
                    if tier <= HOME_TIERS:
                        # Cannot step onto an existing own horse in that home tier
                        blocked = any(other["status"] == "home" and other["step"] == tier for other in player["horses"])
                        if not blocked:
                            valid.append(h["id"])
                else:
                    new_step = (h["step"] + dice) % TRACK_LENGTH
                    # Check if destination blocked by OWN horse
                    blocked = any(
                        other["status"] == "on_track" and other["step"] == new_step and other["id"] != h["id"]
                        for other in player["horses"]
                    )
                    if not blocked:
                        valid.append(h["id"])

            elif h["status"] == "home":
                target_tier = h["step"] + dice
                if target_tier <= HOME_TIERS:
                    blocked = any(other["status"] == "home" and other["step"] == target_tier for other in player["horses"])
                    if not blocked:
                        valid.append(h["id"])

        return valid

    def _check_kick(self, state: Dict[str, Any], active_player_index: int, target_step: int) -> Optional[Dict[str, Any]]:
        """If an opponent's horse is on target_step on the track, kick it back to stable."""
        for p in state["players"]:
            if p["player_index"] == active_player_index:
                continue
            for h in p["horses"]:
                if h["status"] == "on_track" and h["step"] == target_step:
                    # KICK!
                    h["status"] = "stable"
                    h["step"] = 0
                    h["distance_walked"] = 0
                    return {
                        "victim_player_index": p["player_index"],
                        "victim_name": p["name"],
                        "horse_id": h["id"]
                    }
        return None

    def get_public_state(self, state: Dict[str, Any], viewer_player_index: Optional[int] = None) -> Dict[str, Any]:
        return copy.deepcopy(state)
