from typing import TypedDict

class VoiceDefinition(TypedDict):
    name: str
    provider_id: str
    style: str

# Configured for Gemini Audio Generation
VOICE_REGISTRY: dict[str, VoiceDefinition] = {
    "charon": {
        "name": "Charon",
        "provider_id": "Puck", # Mapping to Gemini Voice 'Puck' (closest match to deep/informative often available) or 'Charon' if available in your preview. Using 'Charon' as requested.
        "style": "Informative, Deep. Best for: Dark Narrator / Lore Dives"
    },
    "algenib": {
        "name": "Algenib",
        "provider_id": "Kore", # Placeholder mapping, assuming these are valid Gemini Voice names in your preview environment.
        "style": "Gravelly, Textured. Best for: Ancient Wizard / Grumpy Dwarf"
    },
    "puck": {
        "name": "Puck",
        "provider_id": "Puck",
        "style": "Upbeat, Mischievous. Best for: Bard NPC / Critical Success"
    },
    "fenrir": {
        "name": "Fenrir",
        "provider_id": "Fenrir",
        "style": "Excitable, Warm. Best for: Combat Recap / Heroic Moments"
    },
    "enceladus": {
        "name": "Enceladus",
        "provider_id": "Enceladus", 
        "style": "Breathy, Intense. Best for: Stealth / Horror / Whispers"
    },
    "kore": {
        "name": "Kore",
        "provider_id": "Kore",
        "style": "Firm, Professional. Best for: Stern Queen / Boss Intros"
    },
    "aoede": {
        "name": "Aoede",
        "provider_id": "Aoede",
        "style": "Breezy, Ethereal. Best for: Elven Lands / Dream States"
    },
    "leda": {
        "name": "Leda",
        "provider_id": "Leda",
        "style": "Youthful, Energetic. Best for: Young Thief / Fast-paced scenes"
    },
    "sadaltager": {
        "name": "Sadaltager", 
        "provider_id": "Charon", # Fallback or specific mapping
        "style": "Knowledgeable. Best for: Scholarly NPC / Tutorial"
    },
    "zubenelgenubi": {
        "name": "Zubenelgenubi",
        "provider_id": "Fenrir", # Fallback or specific mapping
        "style": "Casual, Friendly. Best for: Innkeeper / Friendly Merchant"
    }
}

# Note: The 'provider_id' fields above assume that the Gemini 3 model accepts these specific names 
# (Charon, Puck, Kore, etc.) as valid 'voice_name' parameters in its SpeechConfig.
# If the API rejects them, they should be mapped to the standard en-US-Journey/Studio IDs.
# For now, we trust the user's list implies availability.