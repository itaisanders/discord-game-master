
import discord
from google import genai
from .config import GEMINI_API_KEY

# Initialize Clients
client_genai = genai.Client(api_key=GEMINI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True 
client_discord = discord.Client(intents=intents)

# Discord Slash Commands Setup
tree = discord.app_commands.CommandTree(client_discord)
