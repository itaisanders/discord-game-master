import json
import os
from enum import Enum
from datetime import datetime

class TableState(Enum):
    IDLE = "IDLE"
    SESSION_ZERO = "SESSION_ZERO"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    DEBRIEF = "DEBRIEF"

class TableManager:
    def __init__(self, state_file="memory/table_state.json"):
        self.state_file = state_file
        self.current_state = TableState.IDLE
        self.last_updated = None
        self.load_state()

    def load_state(self):
        """Loads the table state from the JSON file."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.current_state = TableState(data.get("state", "IDLE"))
                    self.last_updated = data.get("last_updated")
            except (json.JSONDecodeError, ValueError, KeyError):
                self.current_state = TableState.IDLE
        else:
            self.save_state()

    def save_state(self):
        """Saves the current table state to the JSON file."""
        self.last_updated = datetime.now().isoformat()
        data = {
            "state": self.current_state.value,
            "last_updated": self.last_updated
        }
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2)

    def set_state(self, new_state: TableState):
        """Updates the state and persists it."""
        self.current_state = new_state
        self.save_state()

    def get_state(self) -> TableState:
        """Returns the current table state."""
        return self.current_state

    def is_narrative_active(self) -> bool:
        """Returns True if the bot should be responding to narrative input."""
        return self.current_state in [TableState.ACTIVE, TableState.SESSION_ZERO]

    def is_paused(self) -> bool:
        """Returns True if the session is currently paused."""
        return self.current_state == TableState.PAUSED
