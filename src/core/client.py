
import discord
from google import genai
from .config import GEMINI_API_KEY, LLM_PROVIDER
from .llm import ProviderFactory

# Initialize Clients
# client_genai is kept for backward compatibility if needed, but we should move to llm_provider
client_genai = genai.Client(api_key=GEMINI_API_KEY, http_options={'api_version': 'v1beta'})

# New Modular Provider
llm_provider = ProviderFactory.get_provider(LLM_PROVIDER, api_key=GEMINI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True 
client_discord = discord.Client(intents=intents)

# Discord Slash Commands Setup
tree = discord.app_commands.CommandTree(client_discord)
