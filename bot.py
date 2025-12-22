
import os
import sys
import discord
from google import genai
from google.genai import types
from dotenv import load_dotenv

# 1. Setup & Configuration
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
STORE_ID = os.getenv("STORE_ID")
TARGET_CHANNEL_ID_STR = os.getenv("TARGET_CHANNEL_ID")
PERSONA_FILE = os.getenv("PERSONA_FILE")
AI_MODEL = os.getenv("AI_MODEL")

# Basic validation
if not all([DISCORD_TOKEN, GEMINI_API_KEY, STORE_ID, TARGET_CHANNEL_ID_STR]):
    print("❌ Error: Missing environment variables. Please check .env")
    exit(1)

try:
    TARGET_CHANNEL_ID = int(TARGET_CHANNEL_ID_STR)
except ValueError:
    print("❌ Error: TARGET_CHANNEL_ID must be an integer.")
    exit(1)

import pathlib

# Load Persona (Dynamic Load)
def load_full_context():
    """Loads the base persona and injects any markdown files from ./knowledge."""
    context_parts = []

    # 1. Load Base Persona
    if os.path.exists(PERSONA_FILE):
        with open(PERSONA_FILE, "r") as f:
            context_parts.append(f.read().strip())
        print(f"✅ Loaded base persona: {PERSONA_FILE}")
    else:
        context_parts.append("You are an amazing Game Master.")
        print(f"⚠️ {PERSONA_FILE} not found, using default instruction.")

    # 2. Inject Knowledge Files (.md)
    knowledge_dir = pathlib.Path("./knowledge")
    injected_files = []
    
    if knowledge_dir.exists():
        for md_file in knowledge_dir.glob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                context_parts.append(f"\n\n--- FILE: {md_file.name} ---\n\n{content}")
                injected_files.append(md_file.name)
            except Exception as e:
                print(f"❌ Failed to load {md_file.name}: {e}")

    if injected_files:
        print(f"📚 Injected Knowledge: {', '.join(injected_files)}")
    else:
        print("ℹ️ No extra markdown knowledge found in ./knowledge")

    return "\n".join(context_parts)

# Initialize System Instruction
FULL_SYSTEM_INSTRUCTION = load_full_context()

# 2. Safety Settings
safety_settings = [
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
]

# 3. Initialize Clients
client_genai = genai.Client(api_key=GEMINI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True 
client_discord = discord.Client(intents=intents)

# -------------------------------------------------------------------------
# TERMINAL MODE LOGIC
# -------------------------------------------------------------------------

def run_terminal_mode():
    """Runs the bot in an interactive terminal loop."""
    print(f"🎮 Terminal Mode: {AI_MODEL}")
    print(f"📖 Persona: {PERSONA_FILE}")
    print(f"📚 RAG Store: {STORE_ID}")
    print("--------------------------------------------------")
    print("Type your message to interact. Type 'exit' to quit.")
    print("--------------------------------------------------")

    local_history = []

    while True:
        try:
            user_input = input("\nUser [@Terminal]: ")
        except KeyboardInterrupt:
            print("\n👋 Session ended.")
            break

        if user_input.lower() in ["exit", "quit"]:
            print("👋 Session ended.")
            break

        print("🤖 GM is typing...", end="\r")

        try:
            # 1. Format history exactly like the Discord bot does
            gemini_history = []
            
            # Reconstruct history from local session state
            for role, text in local_history:
                # Need to wrap user content same as Discord bot: "User [@Name]: text"
                # In local_history, we will store the raw text for simplicity or full text?
                # Let's verify how we store it. 
                # Ideally, we follow the same 'merge' logic.
                
                # Check merge
                if gemini_history and gemini_history[-1].role == role:
                     gemini_history[-1].parts[0].text += "\n" + text
                else:
                    gemini_history.append(types.Content(role=role, parts=[types.Part(text=text)]))

            # Maintain alternation
            if gemini_history and gemini_history[-1].role == "user":
                 gemini_history.append(types.Content(
                    role="model",
                    parts=[types.Part(text="*(Acknowledging context...)*")]
                ))

            # 2. Create Chat Session
            chat = client_genai.chats.create(
                model=AI_MODEL,
                config=types.GenerateContentConfig(
                    system_instruction=FULL_SYSTEM_INSTRUCTION,
                    safety_settings=safety_settings,
                    tools=[types.Tool(
                        file_search=types.FileSearch(
                            file_search_store_names=[STORE_ID]
                        )
                    )]
                ),
                history=gemini_history
            )

            # 3. User Identity Injection
            # We treat the terminal user as "User [@Terminal]"
            formatted_input = f"User [@Terminal]: {user_input}"
            
            response = chat.send_message(formatted_input)
            
            if response.text:
                # Clear line
                print(" " * 20, end="\r")
                print(f"{response.text}")
                
                # Update history with exactly what the model saw/generated
                local_history.append(("user", formatted_input))
                local_history.append(("model", response.text))
            else:
                print("\n(No text response)")

        except Exception as e:
            print(f"\n❌ Error: {e}")

# -------------------------------------------------------------------------
# DISCORD BOT LOGIC
# -------------------------------------------------------------------------

@client_discord.event
async def on_ready():
    print(f'✅ GM Bot logged in as {client_discord.user}')
    print(f'🎯 Authorized Channel: {TARGET_CHANNEL_ID}')

@client_discord.event
async def on_message(message):
    if message.author == client_discord.user:
        return
    if message.channel.id != TARGET_CHANNEL_ID:
        return

    async with message.channel.typing():
        try:
            # Context Continuity: Fetch history
            history_messages = [msg async for msg in message.channel.history(limit=15, before=message)]
            history_messages.reverse()
            
            gemini_history = []
            
            for msg in history_messages:
                content_text = msg.content if msg.content else "[Action/Image]"
                
                # Determine Role and Identity
                is_bot = (msg.author == client_discord.user)
                role = "model" if is_bot else "user"
                
                # Format text with the required @Username mapping
                if not is_bot:
                    formatted_text = f"User [@{msg.author.name}]: {content_text}"
                else:
                    formatted_text = content_text

                # Logic: Merge consecutive turns
                if gemini_history and gemini_history[-1].role == role:
                    current_text = gemini_history[-1].parts[0].text
                    gemini_history[-1].parts[0].text = current_text + "\n" + formatted_text
                else:
                    gemini_history.append(types.Content(
                        role=role,
                        parts=[types.Part(text=formatted_text)]
                    ))

            # Maintain Alternation
            if gemini_history and gemini_history[-1].role == "user":
                gemini_history.append(types.Content(
                    role="model",
                    parts=[types.Part(text="*(Acknowledging history context...)*")]
                ))

            # RAG Tooling
            chat = client_genai.chats.create(
                model=AI_MODEL,
                config=types.GenerateContentConfig(
                    system_instruction=FULL_SYSTEM_INSTRUCTION,
                    safety_settings=safety_settings,
                    tools=[types.Tool(
                        file_search=types.FileSearch(
                            file_search_store_names=[STORE_ID]
                        )
                    )]
                ),
                history=gemini_history
            )

            # Username Injection
            response = chat.send_message(f"User [@{message.author.name}]: {message.content}")
            
            if response.text:
                res_text = response.text
                if len(res_text) > 2000:
                    for i in range(0, len(res_text), 2000):
                        await message.channel.send(res_text[i:i+2000])
                else:
                    await message.channel.send(res_text)

        except Exception as e:
            print(f"❌ GM Technical Error: {e}")
            await message.channel.send(f"⚠️ [Meta: System Error: {e}]")

# -------------------------------------------------------------------------
# ENTRY POINT
# -------------------------------------------------------------------------

if __name__ == "__main__":
    if "--terminal" in sys.argv:
        run_terminal_mode()
    else:
        client_discord.run(DISCORD_TOKEN)