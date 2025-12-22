import os
from dotenv import load_dotenv
import discord
from google import genai

# Load the .env file
load_dotenv()

def verify_setup():
    # 1. Check Discord Token
    token = os.getenv('DISCORD_TOKEN')
    print(f"✅ Discord Token Found: {bool(token)}")

    # 2. Check Gemini API Key
    api_key = os.getenv('GEMINI_API_KEY')
    print(f"✅ Gemini API Key Found: {bool(api_key)}")

    # 3. Test Gemini Client Initialization
    try:
        client = genai.Client(api_key=api_key)
        print("✅ Gemini Client Initialized Successfully!")
    except Exception as e:
        print(f"❌ Gemini Client Error: {e}")

if __name__ == "__main__":
    verify_setup()