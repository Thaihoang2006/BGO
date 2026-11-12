import copy
import random
from typing import Dict, Any, Tuple, Optional, List
from backend.games.base import BaseGameEngine
from backend.games.gem_kingdom.cards_data import (
    GEMS, NOBLES, LEVEL_1_CARDS, LEVEL_2_CARDS, LEVEL_3_CARDS
)

class GemKingdomEngine(BaseGameEngine):
    """Engine for Gem Kingdom (Splendor mechanics).
    Server-authoritative validation for gem tokens, card purchases,
    discounts, reservations, gold jokers, nobles, and 15-point final round.
    """

    def create_initial_state(self, players: List[Dict[str, Any]]) -> Dict[str, Any]:
        num_players = len(players)
        if num_players < 2 or num_players > 4:
            raise ValueError("Gem Kingdom hỗ trợ từ 2 đến 4 người chơi")

        # Bank tokens based on player count
        # 2 players: 4 of each regular gem, 5 gold
        # 3 players: 5 of each regular gem, 5 gold
        # 4 players: 7 of each regular gem, 5 gold
        reg_count = 4 if num_players == 2 else (5 if num_players == 3 else 7)
        bank = {g: reg_count for g in GEMS}
        bank["gold"] = 5

        # Nobles count: players + 1
        shuffled_nobles = copy.deepcopy(NOBLES)
        random.shuffle(shuffled_nobles)
        revealed_nobles = shuffled_nobles[:num_players + 1]

        # Shuffle development decks
        d1 = copy.deepcopy(LEVEL_1_CARDS)
        d2 = copy.deepcopy(LEVEL_2_CARDS)
        d3 = copy.deepcopy(LEVEL_3_CARDS)
        random.shuffle(d1)
        random.shuffle(d2)
        random.shuffle(d3)

        # Draw 4 cards for each level on board
        board_cards = {
            "3": [d3.pop() for _ in range(min(4, len(d3)))],
            "2": [d2.pop() for _ in range(min(4, len(d2)))],
            "1": [d1.pop() for _ in range(min(4, len(d1)))]
        }

        # Player states
        players_state = []
        for p in players:
            players_state.append({
                "player_index": p["player_index"],
                "name": p.get("name", f"Người chơi {p['player_index'] + 1}"),
                "color": p.get("color", "#FF9966"),
                "tokens": {g: 0 for g in GEMS + ["gold"]},
                "bonuses": {g: 0 for g in GEMS},
                "cards": [],
                "reserved_cards": [],
                "nobles": [],
                "prestige_points": 0
            })

        return {
            "game_type": "gem_kingdom",
            "status": "playing", # 'playing', 'finished'
            "current_player": 0,
            "round_number": 1,
            "final_round_triggered": False,
            "bank": bank,
            "nobles": revealed_nobles,
            "board": board_cards,
            "decks_count": {
                "1": len(d1),
                "2": len(d2),
                "3": len(d3)
            },
            "_decks": {
                "1": d1,
                "2": d2,
                "3": d3
            },
            "players": players_state,
            "history": [],
            "pending_discard_player": None, # player_index if token count > 10
            "winner": None
        }

    def validate_action(self, state: Dict[str, Any], player_index: int, action: Dict[str, Any]) -> Tuple[bool, str]:
        if state.get("status") != "playing":
            return False, "Trận đấu đã kết thúc"

        pending_player = state.get("pending_discard_player")
        action_type = action.get("type")

        # If a player has > 10 tokens, they must discard before anything else
        if pending_player is not None:
            if pending_player != player_index:
                return False, f"Đang chờ Người chơi {pending_player + 1} trả bớt token dư thừa"
            if action_type != "discard_tokens":
                return False, "Bạn đang có hơn 10 token, cần thực hiện trả bớt token dư thừa"
        else:
            if state.get("current_player") != player_index:
                return False, "Chưa đến lượt của bạn"

        player = state["players"][player_index]
        bank = state["bank"]

        if action_type == "take_three_gems":
            gems = action.get("gems", [])
            if not isinstance(gems, list) or len(gems) == 0 or len(gems) > 3:
                return False, "Vui lòng chọn từ 1 đến 3 viên đá quý khác màu"

            if len(gems) != len(set(gems)):
                return False, "3 viên đá quý phải khác màu nhau hoàn toàn"

            if "gold" in gems:
                return False, "Không thể lấy token Vàng từ kho chung bằng hành động này"

            for g in gems:
                if g not in GEMS:
                    return False, f"Màu đá quý không hợp lệ: {g}"
                if bank.get(g, 0) < 1:
                    return False, f"Kho chung đã hết đá quý màu {g}"

            # If fewer than 3 gems selected, ensure bank doesn't have other available colors
            available_colors = [g for g in GEMS if bank.get(g, 0) > 0]
            if len(gems) < 3 and len(available_colors) >= 3 and len(gems) < len(available_colors):
                return False, "Khi kho còn từ 3 loại màu trở lên, bạn phải chọn đủ 3 màu khác nhau"

            return True, ""

        elif action_type == "take_two_gems":
            gem = action.get("gem")
            if gem not in GEMS:
                return False, "Màu đá quý không hợp lệ"

            if bank.get(gem, 0) < 4:
                return False, f"Chỉ được lấy 2 viên cùng màu khi kho còn ít nhất 4 viên (hiện có {bank.get(gem, 0)})"

            return True, ""

        elif action_type == "reserve_card":
            if len(player["reserved_cards"]) >= 3:
                return False, "Bạn đã giữ tối đa 3 lá bài dự trữ, không thể dự trữ thêm"

            source = action.get("source") # 'board' or 'deck'
            level = str(action.get("level"))
            if level not in ["1", "2", "3"]:
                return False, "Cấp độ thẻ không hợp lệ (1, 2, 3)"

            if source == "board":
                card_id = action.get("card_id")
                board_row = state["board"].get(level, [])
                card_exists = any(c["id"] == card_id for c in board_row)
                if not card_exists:
                    return False, "Thẻ này không còn trên bàn chơi"
            elif source == "deck":
                deck = state["_decks"].get(level, [])
                if len(deck) == 0:
                    return False, f"Chồng bài cấp {level} đã hết, không thể rút"
            else:
                return False, "Nguồn dự trữ không hợp lệ (chọn 'board' hoặc 'deck')"

            return True, ""

        elif action_type == "buy_card":
            source = action.get("source") # 'board' or 'reserved'
            card_id = action.get("card_id")
            card = None

            if source == "board":
                for lvl in ["1", "2", "3"]:
                    for c in state["board"][lvl]:
                        if c["id"] == card_id:
                            card = c
                            break
                    if card:
                        break
                if not card:
                    return False, "Không tìm thấy thẻ trên bàn chơi"
            elif source == "reserved":
                for c in player["reserved_cards"]:
                    if c["id"] == card_id:
                        card = c
                        break
                if not card:
                    return False, "Không tìm thấy thẻ trong danh sách bài dự trữ của bạn"
            else:
                return False, "Nguồn mua thẻ không hợp lệ"

            # Check if player can afford card
            can_afford, _, _ = self._check_affordability(player, card)
            if not can_afford:
                return False, "Bạn không đủ tài nguyên (đá quý và vàng) để mua thẻ này"

            return True, ""

        elif action_type == "discard_tokens":
            tokens_to_discard = action.get("tokens", {})
            total_discard = sum(tokens_to_discard.values())
            current_total = sum(player["tokens"].values())

            if current_total - total_discard > 10:
                return False, f"Sau khi trả bớt, bạn vẫn còn {current_total - total_discard} token (tối đa cho phép 10)"

            for g, qty in tokens_to_discard.items():
                if qty < 0:
                    return False, "Số lượng token trả phải là số dương"
                if player["tokens"].get(g, 0) < qty:
                    return False, f"Bạn không có đủ {qty} token màu {g} để trả"

            return True, ""

        return False, f"Hành động không xác định: {action_type}"

    def apply_action(self, state: Dict[str, Any], player_index: int, action: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        new_state = copy.deepcopy(state)
        player = new_state["players"][player_index]
        bank = new_state["bank"]
        action_type = action["type"]
        event_data = {"type": action_type, "player_index": player_index}

        if action_type == "take_three_gems":
            gems = action["gems"]
            for g in gems:
                bank[g] -= 1
                player["tokens"][g] += 1
            event_data["gems_taken"] = gems

        elif action_type == "take_two_gems":
            gem = action["gem"]
            bank[gem] -= 2
            player["tokens"][gem] += 2
            event_data["gems_taken"] = [gem, gem]

        elif action_type == "reserve_card":
            source = action["source"]
            level = str(action["level"])
            card = None

            if source == "board":
                card_id = action["card_id"]
                board_row = new_state["board"][level]
                idx = next(i for i, c in enumerate(board_row) if c["id"] == card_id)
                card = board_row.pop(idx)

                # Refill from deck
                deck = new_state["_decks"][level]
                if deck:
                    new_card = deck.pop()
                    board_row.append(new_card)
                    new_state["decks_count"][level] = len(deck)
            else:
                deck = new_state["_decks"][level]
                card = deck.pop()
                new_state["decks_count"][level] = len(deck)

            player["reserved_cards"].append(card)

            # Give 1 gold token if available in bank
            gold_gained = 0
            if bank.get("gold", 0) > 0:
                bank["gold"] -= 1
                player["tokens"]["gold"] += 1
                gold_gained = 1

            event_data["reserved_card_id"] = card["id"]
            event_data["gold_gained"] = gold_gained

        elif action_type == "buy_card":
            source = action["source"]
            card_id = action["card_id"]
            card = None

            if source == "board":
                for lvl in ["1", "2", "3"]:
                    board_row = new_state["board"][lvl]
                    for idx, c in enumerate(board_row):
                        if c["id"] == card_id:
                            card = board_row.pop(idx)
                            deck = new_state["_decks"][lvl]
                            if deck:
                                board_row.append(deck.pop())
                                new_state["decks_count"][lvl] = len(deck)
                            break
                    if card:
                        break
            else:
                idx = next(i for i, c in enumerate(player["reserved_cards"]) if c["id"] == card_id)
                card = player["reserved_cards"].pop(idx)

            # Pay cost
            _, tokens_spent, gold_spent = self._check_affordability(player, card)
            for g, amt in tokens_spent.items():
                player["tokens"][g] -= amt
                bank[g] += amt
            player["tokens"]["gold"] -= gold_spent
            bank["gold"] += gold_spent

            # Add card benefits
            player["cards"].append(card)
            player["bonuses"][card["gem"]] += 1
            player["prestige_points"] += card["points"]

            event_data["bought_card"] = card
            event_data["tokens_spent"] = tokens_spent
            event_data["gold_spent"] = gold_spent

        elif action_type == "discard_tokens":
            tokens_to_discard = action.get("tokens", {})
            for g, qty in tokens_to_discard.items():
                player["tokens"][g] -= qty
                bank[g] += qty
            new_state["pending_discard_player"] = None
            event_data["discarded"] = tokens_to_discard

        # Check for immediate optional discard in take_gems / reserve actions
        discard_included = action.get("discard")
        if discard_included and isinstance(discard_included, dict):
            for g, qty in discard_included.items():
                if 0 < qty <= player["tokens"].get(g, 0):
                    player["tokens"][g] -= qty
                    bank[g] += qty

        # Check total tokens cap (max 10)
        total_tokens = sum(player["tokens"].values())
        if total_tokens > 10:
            new_state["pending_discard_player"] = player_index
            event_data["requires_discard"] = True
            event_data["excess_tokens"] = total_tokens - 10
            return new_state, event_data

        # Check Nobles visit (only after card purchase or turn completion)
        visited_noble = self._check_noble_visit(player, new_state["nobles"])
        if visited_noble:
            # Remove noble from board and award to player
            new_state["nobles"] = [n for n in new_state["nobles"] if n["id"] != visited_noble["id"]]
            player["nobles"].append(visited_noble)
            player["prestige_points"] += visited_noble["points"]
            event_data["noble_visited"] = visited_noble

        # Check 15-point final round trigger
        if player["prestige_points"] >= 15:
            new_state["final_round_triggered"] = True
            event_data["final_round_triggered"] = True

        # Turn Cycling
        num_players = len(new_state["players"])
        is_end_of_round = (player_index == num_players - 1)

        if is_end_of_round:
            new_state["round_number"] += 1
            if new_state["final_round_triggered"]:
                # End of final round: Determine winner!
                new_state["status"] = "finished"
                winner_info = self._determine_winner(new_state["players"])
                new_state["winner"] = winner_info
                event_data["game_over"] = True
                event_data["winner"] = winner_info
                return new_state, event_data

        new_state["current_player"] = (player_index + 1) % num_players
        event_data["next_player"] = new_state["current_player"]
        new_state["history"].append(event_data)

        return new_state, event_data

    def _check_affordability(self, player: Dict[str, Any], card: Dict[str, Any]) -> Tuple[bool, Dict[str, int], int]:
        """Calculates if player can afford card, tokens to pay, and gold used."""
        tokens_spent = {}
        gold_needed = 0

        for g, cost in card.get("cost", {}).items():
            bonus = player["bonuses"].get(g, 0)
            net_cost = max(0, cost - bonus)
            tokens_available = player["tokens"].get(g, 0)

            if tokens_available >= net_cost:
                tokens_spent[g] = net_cost
            else:
                tokens_spent[g] = tokens_available
                gold_needed += (net_cost - tokens_available)

        can_afford = (player["tokens"].get("gold", 0) >= gold_needed)
        return can_afford, tokens_spent, gold_needed

    def _check_noble_visit(self, player: Dict[str, Any], available_nobles: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Check if any noble can visit the player.
        Returns the first matching noble, or None.
        """
        for noble in available_nobles:
            qualifies = True
            for g, req in noble.get("requires", {}).items():
                if player["bonuses"].get(g, 0) < req:
                    qualifies = False
                    break
            if qualifies:
                return noble
        return None

    def _determine_winner(self, players: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Splendor Tie-Breaker:
        1. Highest prestige points.
        2. Fewest development cards purchased.
        """
        sorted_players = sorted(
            players,
            key=lambda p: (p["prestige_points"], -len(p["cards"])),
            reverse=True
        )
        best = sorted_players[0]

        return {
            "player_index": best["player_index"],
            "name": best["name"],
            "color": best["color"],
            "prestige_points": best["prestige_points"],
            "cards_count": len(best["cards"]),
            "nobles_count": len(best["nobles"])
        }

    def get_public_state(self, state: Dict[str, Any], viewer_player_index: Optional[int] = None) -> Dict[str, Any]:
        """Mask opponents' reserved card details if secret, but standard Splendor
        shows who reserved what. Public state mirrors game state without internal decks.
        """
        pub = copy.deepcopy(state)
        pub.pop("_decks", None) # Hide undrawn decks
        return pub
