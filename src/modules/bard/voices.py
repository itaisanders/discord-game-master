from typing import TypedDict

class VoiceDefinition(TypedDict):
    name: str
    provider_id: str
    style: str

# This registry is intended to be configured by the instance owner.
# The provider_id should match the voice IDs supported by the chosen TTS engine (e.g. Gemini).
VOICE_REGISTRY: dict[str, VoiceDefinition] = {
    "deep_storyteller": {
        "name": "The Ancient One",
        "provider_id": "en-US-Studio-O", # Example Google Cloud TTS / Gemini ID
        "style": "Deep, resonant, slow pacing, mythological tone"
    },
    "energetic_bard": {
        "name": "Jaskier",
        "provider_id": "en-GB-Studio-B",
        "style": "Fast, whimsical, higher pitch, tavern-tale tone"
    },
    "shadow_whisperer": {
        "name": "The Shadow",
        "provider_id": "en-US-Neural2-D",
        "style": "Raspy, intimate, dark and mysterious tone"
    }
}
