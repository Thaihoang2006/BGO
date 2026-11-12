from typing import Dict, Type
from backend.games.base import BaseGameEngine
from backend.games.caro.engine import CaroEngine
from backend.games.gem_kingdom.engine import GemKingdomEngine
from backend.games.ludo.engine import LudoEngine
from backend.games.monopoly.engine import MonopolyEngine
from backend.games.undercover.engine import UndercoverEngine

ENGINES: Dict[str, BaseGameEngine] = {
    "caro": CaroEngine(),
    "gem_kingdom": GemKingdomEngine(),
    "ludo": LudoEngine(),
    "monopoly": MonopolyEngine(),
    "undercover": UndercoverEngine(),
}

def get_game_engine(game_type: str) -> BaseGameEngine:
    if game_type not in ENGINES:
        raise ValueError(f"Game type '{game_type}' is not supported yet or invalid.")
    return ENGINES[game_type]

__all__ = [
    "BaseGameEngine",
    "CaroEngine",
    "GemKingdomEngine",
    "LudoEngine",
    "MonopolyEngine",
    "UndercoverEngine",
    "get_game_engine",
    "ENGINES"
]
