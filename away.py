import json
import os
import time
from typing import Dict, Optional, List

class AwayManager:
    """
    Manages player absence states.
    Persistence: stored in memory/away_status.json
    """
    
    VALID_MODES = ["auto-pilot", "off-screen", "narrative-exit"]

    def __init__(self, filepath: str = "memory/away_status.json"):
        self.filepath = filepath
        self.data: Dict[str, Dict] = {}
        self._load()

    def _load(self):
        """Loads away status from JSON file."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️ Failed to load away status from {self.filepath}: {e}")
                self.data = {}
        else:
            self.data = {}

    def _save(self):
        """Saves current state to JSON file."""
        try:
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2)
        except IOError as e:
            print(f"❌ Failed to save away status: {e}")

    def set_away(self, user_id: str, mode: str, last_seen_message_id: int) -> bool:
        """
        Marks a user as away.
        Returns True if successful, False if validation fails.
        """
        if mode not in self.VALID_MODES:
            print(f"❌ Invalid away mode: {mode}. Valid: {self.VALID_MODES}")
            return False

        self.data[user_id] = {
            "mode": mode,
            "last_seen_message_id": last_seen_message_id,
            "timestamp": time.time()
        }
        self._save()
        return True

    def return_user(self, user_id: str) -> Optional[Dict]:
        """
        Marks a user as back (active). 
        Returns their previous away data (for summary generation) or None if they weren't away.
        """
        if user_id in self.data:
            away_data = self.data.pop(user_id)
            self._save()
            return away_data
        return None

    def is_away(self, user_id: str) -> bool:
        """Checks if a user is currently away."""
        return user_id in self.data

    def get_away_data(self, user_id: str) -> Optional[Dict]:
        """Returns the specific data for an away user."""
        return self.data.get(user_id)

    def get_all_away_users(self) -> Dict[str, Dict]:
        """Returns a dictionary of all currently away users."""
        return self.data.copy()
