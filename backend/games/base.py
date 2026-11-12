from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional, List

class BaseGameEngine(ABC):
    """Abstract base class for all BGO game engines.
    Ensures server-authoritative rule enforcement, turn cycling,
    state immutability / versioning, and validation.
    """

    @abstractmethod
    def create_initial_state(self, players: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate initial game state for given players."""
        pass

    @abstractmethod
    def validate_action(self, state: Dict[str, Any], player_index: int, action: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate if player_index can execute action on state.
        Returns (is_valid, error_message).
        """
        pass

    @abstractmethod
    def apply_action(self, state: Dict[str, Any], player_index: int, action: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Apply action to state and return (updated_state, event_data).
        Must only be called after validate_action passes.
        """
        pass

    @abstractmethod
    def get_public_state(self, state: Dict[str, Any], viewer_player_index: Optional[int] = None) -> Dict[str, Any]:
        """Return state safe for frontend consumption (masking hidden info if any)."""
        pass
