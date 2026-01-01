
import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TARGET_CHANNEL_ID_STR = os.getenv("TARGET_CHANNEL_ID")

AI_MODEL = os.getenv("AI_MODEL", "gemini-2.0-flash-lite")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")

# Model Overrides per Persona/Function
MODEL_GM = os.getenv("MODEL_GM", AI_MODEL)
MODEL_ARCHITECT = os.getenv("MODEL_ARCHITECT", AI_MODEL)
MODEL_VISUAL = os.getenv("MODEL_VISUAL", "gemini-2.5-flash-image") # Default for visuals
MODEL_FEEDBACK = os.getenv("MODEL_FEEDBACK", AI_MODEL)
GEMINI_AUDIO_MODEL = os.getenv("GEMINI_AUDIO_MODEL", "gemini-2.0-flash")

TARGET_CHANNEL_ID = 0
try:
    if TARGET_CHANNEL_ID_STR:
        TARGET_CHANNEL_ID = int(TARGET_CHANNEL_ID_STR)
except ValueError:
    print("❌ Error: TARGET_CHANNEL_ID must be an integer.")
    exit(1)

def validate_config():
    if not all([DISCORD_TOKEN, GEMINI_API_KEY, TARGET_CHANNEL_ID_STR]):
        return False
    return True
