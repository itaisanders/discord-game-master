
import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TARGET_CHANNEL_ID_STR = os.getenv("TARGET_CHANNEL_ID")

AI_MODEL = os.getenv("AI_MODEL", "gemini-2.0-flash-lite")

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
