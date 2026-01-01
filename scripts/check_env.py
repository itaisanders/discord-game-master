import os
import sys
import pathlib
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.llm import ProviderFactory

# Load the .env file
load_dotenv()

def verify_setup():
    # 1. Check Discord Token
    token = os.getenv('DISCORD_TOKEN')
    print(f"✅ Discord Token Found: {bool(token)}")

    # 2. Check Provider and Keys
    provider = os.getenv('LLM_PROVIDER', 'gemini')
    api_key = os.getenv('GEMINI_API_KEY')
    print(f"✅ LLM Provider: {provider}")
    print(f"✅ Gemini API Key Found: {bool(api_key)}")

    # 3. Test Provider Initialization
    try:
        # We try to initialize via factory
        llm = ProviderFactory.get_provider(provider, api_key=api_key)
        print(f"✅ LLM Provider ({provider}) Initialized Successfully!")
    except Exception as e:
        print(f"❌ LLM Provider Error: {e}")

if __name__ == "__main__":
    verify_setup()

def _syntax_check():
    """A simple function to confirm the file is syntactically correct."""
    return True