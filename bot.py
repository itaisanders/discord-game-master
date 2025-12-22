import os
import sys
import re
import io
import discord
from google import genai
from google.genai import types
from dotenv import load_dotenv
from prettytable import PrettyTable

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
                    formatted_text = f"User [Name: @{msg.author.name}, ID: <@{msg.author.id}>]: {content_text}"
                else:
                    formatted_text = content_text
                    
                    # HISTORY FILTERING: Prevent Ledger Looping
                    # If this bot message contains a Markdown table (detected by separator line), strip it.
                    # This stops the LLM from seeing the table in recent history and repeating it.
                    if "|" in formatted_text and "---" in formatted_text:
                        # Regex to find markdown table blocks:
                        # Looks for the separator row `| --- |` and surrounding pipe-rows
                        table_pattern = r"(\|[^\n]+\|\n\|[- :]+\|(\n\|[^\n]+\|)+)"
                        
                        if re.search(table_pattern, formatted_text):
                            formatted_text = re.sub(table_pattern, "\n*[Master Ledger Table Internalized]*\n", formatted_text)

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

            # Retry Loop for Robustness
            current_model = AI_MODEL
            fallback_triggered = False
            
            for attempt in range(3): # Try up to 3 times
                try:
                    # RAG Tooling
                    chat = client_genai.chats.create(
                        model=current_model,
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

                    # Username Injection & Generation
                    response = chat.send_message(f"User [Name: @{message.author.name}, ID: <@{message.author.id}>]: {message.content}")
                    
                    if response.text:
                        res_text = response.text
                        
                        # -------------------------------------------------------------
                        # DATA_TABLE Parsing & PrettyTable Integration
                        # -------------------------------------------------------------
                        data_table_pattern = r"```DATA_TABLE\n(.*?)```"
                        
                        def render_table_as_ascii(match):
                            table_block = match.group(1)
                            try:
                                lines = [l.strip() for l in table_block.strip().split('\n') if l.strip()]
                                title = "Data Table"
                                headers = []
                                rows = []
                                
                                for line in lines:
                                    if line.startswith("Title:"):
                                        title = line.replace("Title:", "").strip()
                                    elif "|" in line:
                                        cols = [c.strip() for c in line.split('|')]
                                        if not headers:
                                            headers = cols
                                        else:
                                            rows.append(cols)
                                
                                if headers:
                                    pt = PrettyTable()
                                    pt.field_names = headers
                                    pt.align = "l"
                                    pt.border = True
                                    
                                    # Note: Horizontal wrapping for mobile if columns > 5
                                    # ASCII tables don't naturally wrap, so we keep it standard 
                                    # but acknowledge the constraint for readability.
                                    for row in rows:
                                        # Fill missing columns with empty string if row is too short
                                        if len(row) < len(headers):
                                            row.extend([""] * (len(headers) - len(row)))
                                        pt.add_row(row[:len(headers)]) # Ensure row isn't too long
                                    
                                    return f"**{title}**\n```text\n{pt.get_string()}\n```"
                            except Exception as e:
                                print(f"⚠️ Failed to parse DATA_TABLE: {e}")
                                return match.group(0) # Fallback to raw text
                            return match.group(0)

                        # Replace all DATA_TABLE blocks with ASCII versions
                        res_text = re.sub(data_table_pattern, render_table_as_ascii, res_text, flags=re.DOTALL).strip()
                        
                        # -------------------------------------------------------------
                        # VISUAL_PROMPT Parsing & Image Generation
                        # -------------------------------------------------------------
                        visual_prompt_pattern = r"```VISUAL_PROMPT\n(.*?)```"
                        visual_match = re.search(visual_prompt_pattern, res_text, re.DOTALL)
                        generated_file = None
                        
                        if visual_match:
                            prompt_text = visual_match.group(1).strip()
                            
                            # STYLEGUIDE INJECTION: Append content of .style files for consistency
                            style_dir = pathlib.Path("./knowledge")
                            if style_dir.exists():
                                style_files = list(style_dir.glob("*.style"))
                                if style_files:
                                    style_refs = []
                                    for sf in style_files:
                                        try:
                                            style_refs.append(f"\n--- STYLE REFERENCE: {sf.name} ---\n{sf.read_text(encoding='utf-8')}")
                                        except Exception as e:
                                            print(f"⚠️ Failed to read style file {sf.name}: {e}")
                                    
                                    if style_refs:
                                        prompt_text += "\n\n[MANDATORY STYLE INSTRUCTIONS]:" + "".join(style_refs)

                            # Clean the prompt from the response
                            res_text = re.sub(visual_prompt_pattern, "", res_text, flags=re.DOTALL).strip()
                            
                            try:
                                # Nano Banana Image Generation
                                img_response = client_genai.models.generate_content(
                                    model="gemini-2.5-flash-image",
                                    contents=prompt_text
                                )
                                
                                # Access generated image bytes
                                # The SDK usually returns this in candidates -> parts -> data
                                # or candidates -> parts -> inline_data. For Imagen models it might vary.
                                # Following user request for nano banana:
                                if hasattr(img_response, 'generated_images') and img_response.generated_images:
                                    image_bytes = img_response.generated_images[0].image.image_bytes
                                    generated_file = discord.File(io.BytesIO(image_bytes), filename="visual.png")
                                elif img_response.candidates and img_response.candidates[0].content.parts:
                                    # Fallback for standard multimodal response
                                    part = img_response.candidates[0].content.parts[0]
                                    if part.inline_data:
                                        generated_file = discord.File(io.BytesIO(part.inline_data.data), filename="visual.png")
                                
                                if not generated_file:
                                    # Try to find a reason in candidates (e.g. SAFETY)
                                    finish_reason = "Unknown"
                                    if img_response.candidates:
                                        finish_reason = img_response.candidates[0].finish_reason
                                    res_text += f"\n\n*The mists of the Spire obscure your vision... (Image failed: {finish_reason})*"
                            except Exception as e:
                                err_str = str(e)
                                # Make safety errors more readable
                                if "SAFETY" in err_str.upper():
                                    err_str = "Safety block triggered (Prompt violates visual safety policies)"
                                print(f"❌ Image Generation Failed: {e}")
                                res_text += f"\n\n*The mists of the Spire obscure your vision... (Technical Error: {err_str})*"

                        # -------------------------------------------------------------
                        # Sending Logic
                        # -------------------------------------------------------------
                        if len(res_text) > 2000:
                            parts = [res_text[i:i+2000] for i in range(0, len(res_text), 2000)]
                            for i, chunk in enumerate(parts):
                                if i == len(parts) - 1 and generated_file:
                                    await message.channel.send(chunk, file=generated_file)
                                else:
                                    await message.channel.send(chunk)
                        else:
                            if generated_file:
                                await message.channel.send(res_text, file=generated_file)
                            else:
                                await message.channel.send(res_text)
                        
                        break # Success - Exit Loop

                except Exception as e:
                    error_str = str(e)
                    
                    # Check if this is a retryable rate limit error
                    if "RESOURCE_EXHAUSTED" in error_str:
                        import asyncio
                        
                        # LAST ATTEMPT CHECK
                        if attempt == 2:
                            await message.channel.send(f"❌ Failed after 3 attempts. Please try again later.\nError: {e}")
                            break

                        # 1. Parse Duration
                        wait_time_match = re.search(r"Please retry in (\d+\.?\d*)s", error_str)
                        if wait_time_match:
                            wait_s = float(wait_time_match.group(1))
                            msg = f"⚠️ Rate limit reached. Cooling down... I will attempt to answer again in {wait_s} seconds."
                        else:
                            wait_s = 60 # Default cool down
                            msg = f"⚠️ Rate limit reached. Cooling down... I will attempt to answer again in {wait_s} seconds."
                            
                            # 2. Model Fallback Check (Daily Quota)
                            if ("Quota" in error_str or "quota" in error_str) and not fallback_triggered:
                                fallback_triggered = True
                                current_model = "gemini-1.5-flash-8b"
                                msg = f"⚠️ Daily Quota exhausted. Switching to fallback model: **{current_model}**. Retrying in {wait_s}s..."

                        # 3. Notify & Wait
                        print(f"⏳ Retry {attempt+1}/3: Waiting {wait_s}s... ({error_str})")
                        await message.channel.send(msg)
                        await asyncio.sleep(wait_s)
                        continue # Retry
                    
                    else:
                        # Non-retryable error
                        print(f"❌ GM Technical Error: {e}")
                        await message.channel.send(f"⚠️ [Meta: System Error: {e}]")
                        break

        except Exception as e:
            print(f"❌ General Logic Error: {e}")
            await message.channel.send(f"⚠️ [Meta: System Logic Error: {e}]")

# -------------------------------------------------------------------------
# ENTRY POINT
# -------------------------------------------------------------------------

if __name__ == "__main__":
    if "--terminal" in sys.argv:
        run_terminal_mode()
    else:
        client_discord.run(DISCORD_TOKEN)
