"""Undercover Game Engine for BGO (Board Games Online).
Supports 3-20 official players, spectator viewing, secret roles,
turn-based descriptions, voting, tie re-votes, and Mr. White deduction guessing.
"""

import copy
import random
import re
import unicodedata
from typing import Dict, Any, Tuple, Optional, List
from backend.games.base import BaseGameEngine
from backend.games.undercover.words_data import get_word_pair, CATEGORIES


def strip_accents(text: str) -> str:
    """Remove Vietnamese diacritics and normalize to lowercase ASCII."""
    if not text:
        return ""
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = text.replace("đ", "d").replace("Đ", "d")
    return text.lower().strip()


def normalize_guess(text: str) -> str:
    """Clean guess string: strip accents, punctuation, and extra whitespace."""
    s = strip_accents(text)
    s = re.sub(r"[^\w\s]", "", s)
    return "".join(s.split())


class UndercoverEngine(BaseGameEngine):
    """Server-authoritative engine for Undercover (Ai Là Gián Điệp?)."""

    @staticmethod
    def get_default_role_counts(num_players: int) -> Tuple[int, int, int]:
        """Returns recommended (civilians, undercovers, mr_whites) for player count."""
        if num_players < 3:
            num_players = 3
        if num_players <= 5:
            undercover = 1
            mr_white = 0
        elif num_players <= 8:
            undercover = 1
            mr_white = 1
        elif num_players <= 12:
            undercover = 2
            mr_white = 1
        elif num_players <= 16:
            undercover = 3
            mr_white = 1
        else:
            undercover = 4
            mr_white = 2

        civilian = num_players - (undercover + mr_white)
        if civilian < 2:
            civilian = 2
            if undercover > 1:
                undercover -= 1
            elif mr_white > 0:
                mr_white -= 1
        return civilian, undercover, mr_white

    @staticmethod
    def validate_role_counts(num_players: int, undercover: int, mr_white: int) -> Tuple[bool, str]:
        """Validates host's custom role distribution."""
        if undercover < 0 or mr_white < 0:
            return False, "Số lượng vai trò không được âm"
        if undercover + mr_white < 1:
            return False, "Cần có ít nhất 1 Mũ Đen hoặc Mũ Trắng"
        civilians = num_players - (undercover + mr_white)
        if civilians < 2:
            return False, "Cần có ít nhất 2 Dân thường"
        if civilians + undercover + mr_white != num_players:
            return False, f"Tổng số vai trò ({civilians + undercover + mr_white}) phải bằng số người chơi ({num_players})"
        return True, ""

    def create_initial_state(self, players: List[Dict[str, Any]], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate initial game state for given players (3 - 20 players)."""
        num_players = len(players)
        if num_players < 3:
            raise ValueError("Undercover cần tối thiểu 3 người chơi chính thức")
        if num_players > 20:
            raise ValueError("Undercover hỗ trợ tối đa 20 người chơi chính thức")

        options = options or {}
        topic = options.get("topic", "all")
        describe_time = int(options.get("describe_time", 60))
        vote_time = int(options.get("vote_time", 45))
        reveal_role = bool(options.get("reveal_role_on_elimination", True))

        # Role counts
        if "undercover_count" in options and "mrwhite_count" in options:
            undercover_c = int(options["undercover_count"])
            mrwhite_c = int(options["mrwhite_count"])
            valid, msg = self.validate_role_counts(num_players, undercover_c, mrwhite_c)
            if not valid:
                raise ValueError(msg)
            civilian_c = num_players - (undercover_c + mrwhite_c)
        else:
            civilian_c, undercover_c, mrwhite_c = self.get_default_role_counts(num_players)

        # Select word pair
        word_civilian, word_undercover, pair_meta = get_word_pair(category=topic)

        # Assign roles randomly
        role_list = (["civilian"] * civilian_c) + (["undercover"] * undercover_c) + (["mr_white"] * mrwhite_c)
        random.shuffle(role_list)

        # Build player states
        players_state = []
        for idx, p in enumerate(players):
            role = role_list[idx]
            if role == "civilian":
                w = word_civilian
            elif role == "undercover":
                w = word_undercover
            else:
                w = ""

            players_state.append({
                "player_index": p["player_index"],
                "name": p["name"],
                "color": p.get("color", "#FF9966"),
                "symbol": p.get("symbol", str(idx + 1)),
                "role": role,
                "word": w,
                "is_alive": True,
                "has_confirmed": False,
                "eliminated_at_round": None
            })

        # Turn order for describing: randomized
        turn_order = [p["player_index"] for p in players_state]
        random.shuffle(turn_order)

        state = {
            "game_type": "undercover",
            "phase": "describe",  # Describe immediately: Vòng 1 bắt đầu ngay lập tức
            "round_number": 1,
            "secret_words": {
                "civilian": word_civilian,
                "undercover": word_undercover
            },
            "word_pair_info": {
                "id": pair_meta["id"],
                "category": pair_meta["category"],
                "category_name": CATEGORIES.get(pair_meta["category"], pair_meta["category"])
            },
            "players": players_state,
            "turn_order": turn_order,
            "current_turn_index": 0,
            "current_player": turn_order[0] if turn_order else 0,
            "descriptions": {},  # round_str -> list of desc dicts
            "votes": {},  # str(voter_index) -> target_index
            "vote_tallies": {},  # str(target_index) -> count
            "revote_candidates": [],
            "is_revote": False,
            "pending_mrwhite": None,  # player_index guessing civilian word
            "winner": None,
            "settings": {
                "describe_time": describe_time,
                "vote_time": vote_time,
                "reveal_role_on_elimination": reveal_role,
                "undercover_count": undercover_c,
                "mrwhite_count": mrwhite_c,
                "civilian_count": civilian_c,
                "topic": topic
            },
            "history_log": [
                f"Ván đấu bắt đầu với {num_players} người chơi ({civilian_c} Dân thường, {undercover_c} Mũ Đen, {mrwhite_c} Mũ Trắng)."
            ]
        }
        return state

    def validate_action(self, state: Dict[str, Any], player_index: int, action: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate if player_index can execute action on state."""
        action_type = action.get("type")
        phase = state.get("phase")

        if not action_type:
            return False, "Thiếu action type"

        if phase == "finished" and action_type != "rematch":
            return False, "Ván đấu đã kết thúc"

        player = next((p for p in state["players"] if p["player_index"] == player_index), None)
        if not player:
            return False, "Người chơi không tồn tại trong ván đấu"

        if action_type in ("confirm_secret", "start_descriptions"):
            return True, ""

        if action_type == "submit_description":
            if phase != "describe":
                return False, "Hiện không phải giai đoạn mô tả"
            if not player["is_alive"]:
                return False, "Người chơi đã bị loại không thể mô tả"
            if state.get("current_player") != player_index:
                return False, f"Chưa đến lượt của bạn (Đang là lượt của {self._get_player_name(state, state.get('current_player'))})"
            text = (action.get("text") or "").strip()
            if not text:
                return False, "Nội dung mô tả không được để trống"
            if len(text) > 250:
                return False, "Mô tả tối đa 250 ký tự"

            # Check if player directly mentions their secret word
            if player["role"] != "mr_white" and player.get("word"):
                word_clean = strip_accents(player["word"])
                text_clean = strip_accents(text)
                if word_clean in text_clean:
                    return False, f"Không được nhắc trực tiếp từ khóa '{player['word']}' trong lời mô tả!"
            return True, ""

        if action_type == "pass_description":
            if phase != "describe":
                return False, "Hiện không phải giai đoạn mô tả"
            if not player["is_alive"]:
                return False, "Người chơi đã bị loại không thể mô tả"
            if state.get("current_player") != player_index:
                return False, "Chưa đến lượt của bạn"
            return True, ""

        if action_type == "end_discussion":
            if phase != "discuss":
                return False, "Hiện không phải giai đoạn thảo luận"
            return True, ""

        if action_type == "submit_vote":
            if phase != "vote":
                return False, "Hiện không phải giai đoạn bỏ phiếu"
            if not player["is_alive"]:
                return False, "Người chơi đã bị loại không có quyền bỏ phiếu"
            target = action.get("target_player_index")
            if target is None:
                return False, "Thiếu người được bỏ phiếu"
            if target == player_index:
                return False, "Không được tự bỏ phiếu cho chính mình"
            target_player = next((p for p in state["players"] if p["player_index"] == target), None)
            if not target_player or not target_player["is_alive"]:
                return False, "Người được bỏ phiếu không hợp lệ hoặc đã bị loại"
            revote_cands = state.get("revote_candidates", [])
            if revote_cands and target not in revote_cands:
                return False, "Trong vòng hòa phiếu, chỉ được bỏ phiếu cho người trong danh sách hòa"
            return True, ""

        if action_type == "tally_votes":
            if phase != "vote":
                return False, "Không ở giai đoạn bỏ phiếu"
            return True, ""

        if action_type == "mrwhite_guess":
            if phase != "mrwhite_guess":
                return False, "Hiện không phải giai đoạn Mũ Trắng đoán từ"
            if state.get("pending_mrwhite") != player_index:
                return False, "Bạn không phải Mũ Trắng đang được quyền đoán từ"
            guess = (action.get("guess") or "").strip()
            if not guess:
                return False, "Từ đoán không được để trống"
            return True, ""

        if action_type == "rematch":
            if phase != "finished":
                return False, "Chỉ có thể tái đấu khi ván kết thúc"
            return True, ""

        return False, f"Hành động không xác định: {action_type}"

    def apply_action(self, state: Dict[str, Any], player_index: int, action: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Apply validated action to state and return (updated_state, event_data)."""
        new_state = copy.deepcopy(state)
        action_type = action.get("type")
        event = {"action": action_type, "player_index": player_index}

        player = next(p for p in new_state["players"] if p["player_index"] == player_index)

        if action_type == "confirm_secret":
            player["has_confirmed"] = True
            all_confirmed = all(p["has_confirmed"] for p in new_state["players"])
            event["all_confirmed"] = all_confirmed
            if all_confirmed:
                self._start_describe_phase(new_state)

        elif action_type == "start_descriptions":
            self._start_describe_phase(new_state)

        elif action_type in ("submit_description", "pass_description"):
            rnd_key = str(new_state["round_number"])
            if rnd_key not in new_state["descriptions"]:
                new_state["descriptions"][rnd_key] = []

            is_pass = (action_type == "pass_description")
            text = "(Bỏ lượt)" if is_pass else action.get("text", "").strip()
            desc_record = {
                "round": new_state["round_number"],
                "player_index": player_index,
                "player_name": player["name"],
                "color": player["color"],
                "text": text,
                "passed": is_pass
            }
            new_state["descriptions"][rnd_key].append(desc_record)
            new_state["history_log"].append(f"{player['name']}: {text}")
            event["description"] = desc_record

            # Advance turn
            turn_order = new_state.get("turn_order", [])
            new_state["current_turn_index"] += 1
            if new_state["current_turn_index"] < len(turn_order):
                new_state["current_player"] = turn_order[new_state["current_turn_index"]]
            else:
                # All alive players in this round have described -> proceed directly to vote!
                new_state["phase"] = "vote"
                new_state["votes"] = {}
                new_state["vote_tallies"] = {}
                new_state["revote_candidates"] = []
                new_state["is_revote"] = False
                new_state["current_player"] = None
                new_state["history_log"].append(
                    f"Vòng {new_state['round_number']}: Tất cả người chơi đã mô tả xong. Bắt đầu bỏ phiếu loại gián điệp!"
                )

        elif action_type == "end_discussion":
            new_state["phase"] = "vote"
            new_state["votes"] = {}
            new_state["vote_tallies"] = {}
            new_state["revote_candidates"] = []
            new_state["is_revote"] = False
            new_state["history_log"].append(f"Vòng {new_state['round_number']}: Chuyển sang giai đoạn Bỏ phiếu!")

        elif action_type == "submit_vote":
            target = action["target_player_index"]
            new_state["votes"][str(player_index)] = target
            event["voted_target"] = target
            alive_count = sum(1 for p in new_state["players"] if p["is_alive"])
            if len(new_state["votes"]) >= alive_count:
                # All alive players have cast their votes -> tally immediately
                self._tally_votes(new_state, event)

        elif action_type == "tally_votes":
            self._tally_votes(new_state, event)

        elif action_type == "mrwhite_guess":
            guess = (action.get("guess") or "").strip()
            civ_word = new_state["secret_words"]["civilian"]
            is_correct = (normalize_guess(guess) == normalize_guess(civ_word))

            event["guess"] = guess
            event["is_correct"] = is_correct

            if is_correct:
                # Mr. White wins immediately!
                new_state["winner"] = {
                    "team": "mr_white",
                    "player_index": player_index,
                    "player_name": player["name"],
                    "reason": f"Mũ Trắng ({player['name']}) đã đoán chính xác từ khóa của Dân thường: '{civ_word}'!"
                }
                new_state["phase"] = "finished"
                new_state["history_log"].append(
                    f"Mũ Trắng {player['name']} đoán '{guess}' -> CHÍNH XÁC! Mũ Trắng chiến thắng ngoạn mục!"
                )
            else:
                new_state["history_log"].append(
                    f"Mũ Trắng {player['name']} đoán '{guess}' -> KHÔNG CHÍNH XÁC! (Đáp án không phải từ đó)."
                )
                new_state["pending_mrwhite"] = None
                # Check win condition for remaining players
                self._check_win_conditions(new_state)

        elif action_type == "rematch":
            # Restart game with new word pair, keeping same players
            options = {
                "topic": new_state["settings"].get("topic", "all"),
                "describe_time": new_state["settings"].get("describe_time", 60),
                "vote_time": new_state["settings"].get("vote_time", 45),
                "reveal_role_on_elimination": new_state["settings"].get("reveal_role_on_elimination", True),
                "undercover_count": new_state["settings"].get("undercover_count"),
                "mrwhite_count": new_state["settings"].get("mrwhite_count")
            }
            new_state = self.create_initial_state(new_state["players"], options)
            event["rematch_started"] = True

        return new_state, event

    def _start_describe_phase(self, state: Dict[str, Any]):
        """Transitions state to describe phase."""
        state["phase"] = "describe"
        # Alive players only in turn order
        alive_indices = [p["player_index"] for p in state["players"] if p["is_alive"]]
        random.shuffle(alive_indices)
        state["turn_order"] = alive_indices
        state["current_turn_index"] = 0
        state["current_player"] = alive_indices[0] if alive_indices else 0
        state["history_log"].append(f"Vòng {state['round_number']}: Bắt đầu lượt mô tả từ khóa!")

    def _tally_votes(self, state: Dict[str, Any], event: Dict[str, Any]):
        """Tallies votes and handles eliminations or tie revotes."""
        votes = state.get("votes", {})
        tallies: Dict[int, int] = {}
        for voter_str, target in votes.items():
            tallies[target] = tallies.get(target, 0) + 1

        state["vote_tallies"] = {str(k): v for k, v in tallies.items()}
        event["vote_tallies"] = state["vote_tallies"]

        if not tallies:
            # Nobody voted, proceed to next round without elimination
            state["history_log"].append("Không có phiếu bầu nào được gửi. Không ai bị loại!")
            self._start_next_round(state)
            return

        max_votes = max(tallies.values())
        top_candidates = [cand for cand, count in tallies.items() if count == max_votes]

        if len(top_candidates) > 1:
            # Tie detected
            if not state.get("is_revote", False):
                # First tie: trigger revote between top candidates
                state["is_revote"] = True
                state["revote_candidates"] = top_candidates
                state["votes"] = {}
                state["vote_tallies"] = {}
                cand_names = [self._get_player_name(state, c) for c in top_candidates]
                state["history_log"].append(f"Hòa phiếu giữa: {', '.join(cand_names)} ({max_votes} phiếu). Tiến hành bỏ phiếu lại giữa các người chơi này!")
                event["tie_revote"] = top_candidates
                return
            else:
                # Second consecutive tie: skip elimination
                state["history_log"].append("Tiếp tục hòa phiếu ở vòng bỏ phiếu lại. Không ai bị loại ở vòng này!")
                self._start_next_round(state)
                return

        # Single player with highest votes is eliminated
        eliminated_index = top_candidates[0]
        eliminated_player = next((p for p in state["players"] if p["player_index"] == eliminated_index), None)
        if not eliminated_player:
            self._start_next_round(state)
            return

        eliminated_player["is_alive"] = False
        eliminated_player["eliminated_at_round"] = state["round_number"]
        event["eliminated"] = {
            "player_index": eliminated_index,
            "name": eliminated_player["name"],
            "role": eliminated_player["role"]
        }

        role_str = "Mũ Trắng" if eliminated_player["role"] == "mr_white" else ("Mũ Đen" if eliminated_player["role"] == "undercover" else "Dân thường")
        state["history_log"].append(f"{eliminated_player['name']} nhận nhiều phiếu nhất ({max_votes} phiếu) và đã bị LOẠI! (Vai trò: {role_str})")

        # If eliminated player is Mr. White -> give them 1 guess chance!
        if eliminated_player["role"] == "mr_white":
            state["phase"] = "mrwhite_guess"
            state["pending_mrwhite"] = eliminated_index
            state["history_log"].append(f"Mũ Trắng ({eliminated_player['name']}) có cơ hội đoán từ khóa của Dân thường để lật ngược tình thế!")
            return

        # Check standard win conditions
        self._check_win_conditions(state)

    def _check_win_conditions(self, state: Dict[str, Any]):
        """Evaluates win conditions for Civilians vs Specials."""
        alive_civilians = sum(1 for p in state["players"] if p["is_alive"] and p["role"] == "civilian")
        alive_undercovers = sum(1 for p in state["players"] if p["is_alive"] and p["role"] == "undercover")
        alive_mrwhites = sum(1 for p in state["players"] if p["is_alive"] and p["role"] == "mr_white")
        alive_specials = alive_undercovers + alive_mrwhites

        # 1. Civilians win if all specials eliminated
        if alive_specials == 0:
            state["winner"] = {
                "team": "civilian",
                "reason": "Phe Dân thường chiến thắng vì đã loại bỏ toàn bộ Gián điệp (Mũ Đen và Mũ Trắng)!"
            }
            state["phase"] = "finished"
            state["history_log"].append("Phe DÂN THƯỜNG ĐÃ CHIẾN THẮNG!")
            return

        # 2. Specials win if alive civilians <= alive specials
        if alive_civilians <= alive_specials:
            if alive_mrwhites == 0:
                state["winner"] = {
                    "team": "undercover",
                    "reason": "Phe Mũ Đen chiến thắng vì số lượng Gián điệp đã bằng hoặc áp đảo Dân thường!"
                }
                state["history_log"].append("Phe MŨ ĐEN ĐÃ CHIẾN THẮNG!")
            elif alive_undercovers == 0:
                state["winner"] = {
                    "team": "mr_white",
                    "reason": "Mũ Trắng chiến thắng vì đã sống sót và áp đảo số lượng Dân thường!"
                }
                state["history_log"].append("MŨ TRẮNG ĐÃ CHIẾN THẮNG!")
            else:
                state["winner"] = {
                    "team": "specials",
                    "reason": "Phe Gián điệp (Mũ Đen & Mũ Trắng) cùng chiến thắng vì đã áp đảo số lượng Dân thường!"
                }
                state["history_log"].append("PHE GIÁN ĐIỆP (MŨ ĐEN & MŨ TRẮNG) ĐÃ CHIẾN THẮNG!")
            state["phase"] = "finished"
            return

        # Neither condition met -> proceed to next round
        self._start_next_round(state)

    def _start_next_round(self, state: Dict[str, Any]):
        """Advances round number and resets round state."""
        state["round_number"] += 1
        state["votes"] = {}
        state["vote_tallies"] = {}
        state["revote_candidates"] = []
        state["is_revote"] = False
        state["pending_mrwhite"] = None

        # Turn order: rotate or randomize alive players
        alive_indices = [p["player_index"] for p in state["players"] if p["is_alive"]]
        random.shuffle(alive_indices)
        state["turn_order"] = alive_indices
        state["current_turn_index"] = 0
        state["current_player"] = alive_indices[0] if alive_indices else 0
        state["phase"] = "describe"
        state["history_log"].append(f"--- BẮT ĐẦU VÒNG {state['round_number']} ---")

    def _get_player_name(self, state: Dict[str, Any], player_index: Optional[int]) -> str:
        if player_index is None:
            return "Người chơi"
        p = next((x for x in state["players"] if x["player_index"] == player_index), None)
        return p["name"] if p else f"Người chơi {player_index + 1}"

    def get_public_state(self, state: Dict[str, Any], viewer_player_index: Optional[int] = None) -> Dict[str, Any]:
        """Return state safe for frontend consumption (masking hidden secrets).
        Spectators (viewer_player_index is None) and living opponents CANNOT see
        roles or secret words while the match is underway.
        """
        masked = copy.deepcopy(state)
        phase = masked.get("phase")

        # Top-level secret words are ALWAYS removed while match is active
        if phase != "finished":
            masked.pop("secret_words", None)

        reveal_role_on_elim = masked.get("settings", {}).get("reveal_role_on_elimination", True)

        # Set root-level convenience fields for the viewer
        if viewer_player_index is not None:
            me_obj = next((x for x in state.get("players", []) if x["player_index"] == viewer_player_index), None)
            if me_obj:
                masked["my_role"] = me_obj.get("role")
                masked["my_word"] = me_obj.get("word")

        # Mask player roles and words
        for p in masked.get("players", []):
            is_viewer = (viewer_player_index is not None and p["player_index"] == viewer_player_index)
            is_eliminated = not p.get("is_alive", True)

            if phase == "finished":
                # Fully revealed after game finishes
                pass
            elif is_viewer:
                # The viewer can see their own role and word
                pass
            else:
                # Opponent or Spectator
                if is_eliminated and reveal_role_on_elim:
                    # Role is revealed upon elimination, but word remains hidden!
                    p["word"] = "???"
                else:
                    p["role"] = "???"
                    p["word"] = "???"

        # During voting phase, mask other people's targets
        if phase == "vote":
            raw_votes = masked.get("votes", {})
            voted_status = {}
            for voter_str, target in raw_votes.items():
                voter_idx = int(voter_str)
                # Show whether voter has voted
                voted_status[voter_str] = {
                    "has_voted": True,
                    "target": target if (viewer_player_index is not None and voter_idx == viewer_player_index) else None
                }
            masked["votes"] = voted_status

        return masked
