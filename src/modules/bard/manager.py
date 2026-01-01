import json
import os
from datetime import datetime
from .voices import VOICE_REGISTRY, VoiceDefinition

class BardManager:
    def __init__(self, settings_file="memory/bard_settings.json"):
        self.settings_file = settings_file
        self.selected_voice_key = None
        self.last_summary_timestamp = None
        self.load_settings()

    def load_settings(self):
        """Loads bard settings from JSON."""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                    self.selected_voice_key = data.get("selected_voice_key")
                    self.last_summary_timestamp = data.get("last_summary_timestamp")
            except (json.JSONDecodeError, KeyError):
                pass
        
        # Default to first available voice if none selected or invalid
        if self.selected_voice_key not in VOICE_REGISTRY and VOICE_REGISTRY:
            self.selected_voice_key = list(VOICE_REGISTRY.keys())[0]

    def save_settings(self):
        """Persists settings to JSON."""
        data = {
            "selected_voice_key": self.selected_voice_key,
            "last_summary_timestamp": self.last_summary_timestamp
        }
        os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
        with open(self.settings_file, 'w') as f:
            json.dump(data, f, indent=2)

    def get_voice_registry(self) -> dict[str, VoiceDefinition]:
        """Returns the available voice definitions."""
        return VOICE_REGISTRY

    def get_selected_voice(self) -> VoiceDefinition:
        """Returns the currently selected voice definition."""
        return VOICE_REGISTRY.get(self.selected_voice_key)

    def set_selected_voice(self, voice_key: str) -> bool:
        """Sets the selected voice if valid."""
        if voice_key in VOICE_REGISTRY:
            self.selected_voice_key = voice_key
            self.save_settings()
            return True
        return False

    def is_configured(self) -> bool:
        """Returns True if there are voices available to use."""
        return len(VOICE_REGISTRY) > 0

    def update_summary_timestamp(self):
        """Updates the timestamp of the last generated summary."""
        self.last_summary_timestamp = datetime.now().isoformat()
        self.save_settings()
