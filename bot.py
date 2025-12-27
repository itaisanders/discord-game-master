import os
import sys
import re
import io
import discord
from google import genai
from google.genai import types
from dotenv import load_dotenv
from prettytable import PrettyTable
import asyncio
import time
import pathlib
import json
from typing import Optional
from dice import roll
from away import AwayManager

# 1. Setup & Configuration - Load environment variables first
load_dotenv()

# Global state and environment variables (after dotenv loaded)
pending_rolls = {}
away_manager = AwayManager()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TARGET_CHANNEL_ID_STR = os.getenv("TARGET_CHANNEL_ID")
PERSONA_FILE = os.getenv("PERSONA_FILE")
AI_MODEL = os.getenv("AI_MODEL")

# Basic validation
def validate_config():
    if not all([DISCORD_TOKEN, GEMINI_API_KEY, TARGET_CHANNEL_ID_STR]):
        return False
    return True

if __name__ == "__main__":
    if not validate_config():
        print("❌ Error: Missing environment variables. Please check .env")
        exit(1)

try:
    if TARGET_CHANNEL_ID_STR:
        TARGET_CHANNEL_ID = int(TARGET_CHANNEL_ID_STR)
    else:
        TARGET_CHANNEL_ID = 0
except ValueError:
    if __name__ == "__main__":
        print("❌ Error: TARGET_CHANNEL_ID must be an integer.")
        exit(1)
    TARGET_CHANNEL_ID = 0

def get_character_name(user_id: str, user_name: str) -> Optional[str]:
    """
    Finds a character's name by searching the party.ledger for a matching
    Discord User ID or username.
    """
    party_ledger_path = pathlib.Path("./memory/party.ledger")
    if not party_ledger_path.exists():
        return None

    try:
        content = party_ledger_path.read_text(encoding="utf-8")
        lines = content.split('\n')
        
        # Simple table parsing, assuming Name is the first column and User is the second
        # and they are separated by '|'
        for line in lines:
            if not line.strip().startswith('|'):
                continue
                
            cols = [c.strip() for c in line.split('|')]
            if len(cols) > 2:
                name_col = cols[1].replace('**', '').strip()
                user_col = cols[2]
                
                # Check for ID match <@12345> or username match @username
                if f"<@{user_id}>" in user_col or f"@{user_name}" in user_col:
                    return name_col
    except Exception as e:
        print(f"Error parsing party.ledger for character name: {e}")
        return None
    
    return None

# Load Persona (Dynamic Load)
def load_full_context():
    """
    Loads the base persona and injects any markdown files from ./knowledge.
    NOTE: This is intentionally placed after global env vars for FULL_SYSTEM_INSTRUCTION.
    """
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

def load_memory():
    """Loads all .ledger files from ./memory."""
    memory_parts = []
    memory_dir = pathlib.Path("./memory")
    if memory_dir.exists():
        for l_file in memory_dir.glob("*.ledger"):
            try:
                content = l_file.read_text(encoding="utf-8")
                memory_parts.append(f"\n--- CAMPAIGN LEDGER: {l_file.name} ---\n{content}")
            except Exception as e:
                print(f"❌ Failed to load ledger {l_file.name}: {e}")
    return "\n".join(memory_parts)

async def update_ledgers_logic(update_facts):
    """Uses the Memory Architect to update physical ledger files asynchronously."""
    try:
        current_memory = load_memory()
        architect_persona_path = pathlib.Path("personas/memory_architect_persona.md")
        if not architect_persona_path.exists():
            print("⚠️ Memory Architect persona missing!")
            return
            
        persona_content = architect_persona_path.read_text(encoding="utf-8")
        
        prompt = f"# CURRENT LEDGER STATE\n{current_memory if current_memory else '[Empty]'}\n\n# NEW FACTS TO INCORPORATE\n{update_facts}"
        
        # Use AIO client to prevent blocking
        response = await client_genai.aio.models.generate_content(
            model=AI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=persona_content,
                temperature=0.1
            )
        )
        if response.text:
            save_ledger_files(response.text)
    except Exception as e:
        print(f"❌ Ledger Update Error: {e}")

async def reverse_ledgers_logic(facts_to_reverse):
    """Uses the Memory Architect to reverse facts in physical ledger files."""
    try:
        current_memory = load_memory()
        architect_persona_path = pathlib.Path("personas/memory_architect_persona.md")
        if not architect_persona_path.exists():
            print("⚠️ Memory Architect persona missing!")
            return
            
        persona_content = architect_persona_path.read_text(encoding="utf-8")
        
        prompt = (
            f"# CURRENT LEDGER STATE\n{current_memory if current_memory else '[Empty]'}\n\n"
            f"# REWIND EVENT: The following facts are now INCORRECT and must be REVERSED or REMOVED from the ledgers:\n{facts_to_reverse}"
        )
        
        response = await client_genai.aio.models.generate_content(
            model=AI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=persona_content,
                temperature=0.1
            )
        )
        if response.text:
            save_ledger_files(response.text)
            print("⏪ Ledgers Reversed.")
    except Exception as e:
        print(f"❌ Ledger Reversal Error: {e}")

def save_ledger_files(response_text):
    """Parses FILE: blocks from AI response and saves them to ./memory."""
    count = 0
    try:
        # Parse ```FILE: filename.ledger\ncontent\n```
        file_pattern = r"```FILE: (.*?)\n(.*?)```"
        updates = re.findall(file_pattern, response_text, re.DOTALL)
        
        if not updates:
            # Try fallback for non-backticked blocks if any
            file_pattern_nb = r"FILE: (.*?\.ledger)\n(.*?)(?=FILE:|$)"
            updates = re.findall(file_pattern_nb, response_text, re.DOTALL)

        for filename, content in updates:
            filename = filename.strip()
            if not filename.endswith(".ledger"):
                filename += ".ledger"
            
            filepath = pathlib.Path("./memory") / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(content.strip(), encoding="utf-8")
            print(f"💾 Ledger Saved: {filename}")
            count += 1
    except Exception as e:
        print(f"❌ Error saving ledgers: {e}")
    return count


def fetch_character_sheet(character_name: str) -> Optional[str]:
    """
    Loads all .ledger files and searches for a DATA_TABLE block
    representing a character sheet for the given character name.
    Returns the full DATA_TABLE block as a string if found.
    """
    memory_dir = pathlib.Path("./memory")
    if not memory_dir.exists():
        return None

    all_ledger_content = load_memory()
    
    data_table_pattern = r"```DATA_TABLE\s*(.*?)"
    all_tables = re.findall(data_table_pattern, all_ledger_content, re.DOTALL | re.IGNORECASE)
    
    for table_content in all_tables:
        title_pattern = r"Title:\s*(?:Character\s+Sheet:\s*)?(" + re.escape(character_name) + r")\s*"
        if re.search(title_pattern, table_content, re.IGNORECASE):
            return f"```DATA_TABLE\n{table_content}```"
            
    return None

# -------------------------------------------------------------
# PARSING & FORMATTING UTILITIES 
# -------------------------------------------------------------

def process_dice_rolls(text):
    """Intercepts DICE_ROLL protocol blocks and executes actual dice rolls."""
    # Pattern: ```DICE_ROLL\n[Character Name] rolls [dice notation] for [reason]\n```
    dice_pattern = r'```DICE_ROLL\s*(.+?)\s+rolls?\s+([^\s]+)(?:\s+for\s+(.+?))?\s*```'
    
    def replace_with_roll(match):
        character_name = match.group(1).strip()
        notation = match.group(2).strip()
        reason = match.group(3).strip() if match.group(3) else "unknown reason"
        
        result = roll(notation)
        
        if result.error:
            return f"❌ **{character_name}** attempted to roll {notation} but: {result.error}"
        
        return f"🎲 **{character_name}** rolls {notation} for {reason}: {result.formatted}"
    
    processed = re.sub(dice_pattern, replace_with_roll, text, flags=re.DOTALL | re.IGNORECASE)
    
    # Debug logging
    if "DICE_ROLL" in text.upper() and processed != text:
        print("🎲 Intercepted and executed DICE_ROLL block")
    
    return processed

def filter_away_mentions(text):
    """
    Removes mentions (<@ID>) for users who are currently Away.
    This acts as a safety net if the AI hallucinates a tag despite instructions.
    """
    away_users = away_manager.get_all_away_users()
    if not away_users:
        return text

    processed = text
    for user_id in away_users:
        # Check for standard mention format <@123456>
        mention_pattern = rf"<@!?{user_id}>"
        if re.search(mention_pattern, processed):
            print(f"🛡️ Suppressed mention for away user {user_id}")
            # Replace with a generic name reference or just strip it.
            # Stripping it might break grammar, but preventing the ping is priority.
            # We'll replace it with their display name if possible, or just "the character".
            processed = re.sub(mention_pattern, "**(Away)**", processed)
            
    return processed

def process_roll_calls(text):
    """
    Intercepts ROLL_CALL protocol blocks and stores pending rolls.
    
    Format:
    ```ROLL_CALL
    @Username: 2d6+3 for Defy Danger
    ```
    """
    global pending_rolls
    
    roll_call_pattern = r'```ROLL_CALL\s*(.*?)\s*```'
    
    def extract_and_store(match):
        content = match.group(1).strip()
        lines = content.split('\n')
        
        stored_calls = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Parse: @Username: 2d6+3 for Reason
            # We allow optional @
            call_pattern = r'@?(\w+):\s*([^\s]+)(?:\s+for\s+(.+))?'
            call_match = re.match(call_pattern, line, re.IGNORECASE)
            
            if call_match:
                username = call_match.group(1)
                notation = call_match.group(2)
                reason = call_match.group(3).strip() if call_match.group(3) else "unknown"
                
                # Store in pending_rolls keyed by username
                pending_rolls[username] = {
                    "notation": notation,
                    "reason": reason,
                    "timestamp": time.time()
                }
                
                stored_calls.append({
                    "username": username,
                    "notation": notation,
                    "reason": reason
                })
        
        # Return a user-friendly message
        if stored_calls:
            messages = [f"📋 **{call['username']}**, roll {call['notation']} for {call['reason']}" 
                       for call in stored_calls]
            return "\n".join(messages)
        return ""
    
    processed = re.sub(roll_call_pattern, extract_and_store, text, flags=re.DOTALL | re.IGNORECASE)
    
    if "ROLL_CALL" in text.upper() and processed != text:
        print("📋 Intercepted ROLL_CALL block")
    
    return processed

def render_table_as_ascii(match):
    """
    Processes a DATA_TABLE block into a PrettyTable ASCII string.
    """
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
            
            for row in rows:
                if len(row) < len(headers):
                    row.extend(["" ] * (len(headers) - len(row)))
                pt.add_row(row[:len(headers)])
            
            return f"**{title}**\n```text\n{pt.get_string()}\n```"
    except Exception as e:
        print(f"⚠️ Failed to parse DATA_TABLE: {e}")
        return match.group(0)
    return match.group(0)

def process_response_formatting(text):
    """
    Handles all regex-based replacements and extractions (DATA_TABLE, MEMORY_UPDATE, VISUAL_PROMPT).
    """
    
    # 0. Safety Net: Filter Away Mentions
    text = filter_away_mentions(text)

    # 1. DATA_TABLE (Case Insensitive + Flexible Whitespace)
    data_table_pattern = r"```DATA_TABLE\s*(.*?)```"
    if re.search(data_table_pattern, text, re.DOTALL | re.IGNORECASE):
        print("🔍 Found DATA_TABLE block.")
    text = re.sub(data_table_pattern, render_table_as_ascii, text, flags=re.DOTALL | re.IGNORECASE).strip()
    
    memory_update_pattern = r"```MEMORY_UPDATE\s*(.*?)```"
    memory_match = re.search(memory_update_pattern, text, re.DOTALL | re.IGNORECASE)
    facts = None
    if memory_match:
        print("🔍 Found MEMORY_UPDATE block.")
        facts = memory_match.group(1).strip()
        text = re.sub(memory_update_pattern, "", text, flags=re.DOTALL | re.IGNORECASE).strip()
        
    # 3. VISUAL_PROMPT 
    # Primary: Backticked block
    visual_prompt_pattern = r"```VISUAL_PROMPT\s*(.*?)```"
    visual_match = re.search(visual_prompt_pattern, text, re.DOTALL | re.IGNORECASE)
    visual_prompt = None
    if visual_match:
        print("🔍 Found backticked VISUAL_PROMPT.")
        visual_prompt = visual_match.group(1).strip()
        text = re.sub(visual_prompt_pattern, "", text, flags=re.DOTALL | re.IGNORECASE).strip()
    else:
        # Fallback: Header + the Structure brackets (for when AI forgets backticks or uses bolding)
        # We look for the keyword and then any sequence of [...] blocks
        fallback_pattern = r"(?!\*+|#+)?\s*VISUAL_PROMPT\s*(?!\*+|#+)?(?:[:-])?\s*((?:\\\\[.*?\\\\]\s*)+)"
        fallback_match = re.search(fallback_pattern, text, re.DOTALL | re.IGNORECASE)
        if fallback_match:
            print("🔍 Found fallback VISUAL_PROMPT structure.")
            visual_prompt = fallback_match.group(1).strip()
            text = re.sub(fallback_pattern, "", text, flags=re.DOTALL | re.IGNORECASE).strip()

    if not visual_prompt and "VISUAL_PROMPT" in text.upper():
        print("⚠️ Found 'VISUAL_PROMPT' keyword but failed to parse the structure.")
    
    # 4. DICE_ROLL - Intercept and execute actual dice rolls
    text = process_dice_rolls(text)

    # 5. ROLL_CALL - Intercept and queue pending rolls
    text = process_roll_calls(text)

    return text, facts, visual_prompt

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

# Discord Slash Commands Setup
tree = discord.app_commands.CommandTree(client_discord)

@tree.command(name="roll", description="Roll dice (e.g., 2d6+3) or execute pending roll")
async def roll_command(interaction: discord.Interaction, dice: Optional[str] = None):
    """Manual dice roll command for players."""
    
    # 1. Context-Aware Roll (No arguments)
    if dice is None:
        username = interaction.user.name
        if username in pending_rolls:
            pending = pending_rolls[username]
            result = roll(pending["notation"])
            
            if result.error:
                await interaction.response.send_message(f"❌ Invalid pending roll notation: {result.error}", ephemeral=True)
            else:
                # Clear pending roll
                del pending_rolls[username]
                await interaction.response.send_message(
                    f"🎲 **{interaction.user.display_name}** rolls {pending['notation']} for {pending['reason']}: {result.formatted}"
                )
        else:
            await interaction.response.send_message(
                "❌ No pending roll found. Use `/roll [dice]` (e.g., `/roll 2d6+3`).", 
                ephemeral=True
            )
        return

    # 2. Explicit Roll
    result = roll(dice)
    
    if result.error:
        await interaction.response.send_message(f"❌ Invalid dice notation: {result.error}", ephemeral=True)
    else:
        await interaction.response.send_message(
            f"🎲 **{interaction.user.display_name}** rolls {dice}: {result.formatted}"
        )

@tree.command(name="away", description="Mark yourself as away with a specific mode.")
@discord.app_commands.choices(mode=[
    discord.app_commands.Choice(name="Auto-Pilot (GM plays character)", value="auto-pilot"),
    discord.app_commands.Choice(name="Off-Screen (Passive background)", value="off-screen"),
    discord.app_commands.Choice(name="Narrative Exit (Character leaves locally)", value="narrative-exit")
])
async def away_command(interaction: discord.Interaction, mode: discord.app_commands.Choice[str]):
    """Sets the player's status to Away."""
    user_id = str(interaction.user.id)
    # Use the ID of the interaction's message context, or if None, use 0 (though interactions usually have context)
    # We actually want the ID of the last message in the channel effectively. 
    # But since slash commands are ephemeral or separate, getting the exact "last seen" is tricky.
    # We will use the Interaction ID as a proxy or fetch the channel's last message.
    
    last_msg_id = 0
    if interaction.channel and hasattr(interaction.channel, "last_message_id"):
        last_msg_id = interaction.channel.last_message_id
    
    # If last_message_id is None (rare temp channel), use 0
    if not last_msg_id:
        last_msg_id = 0

    success = away_manager.set_away(user_id, mode.value, last_msg_id)
    
    if success:
        await interaction.response.send_message(
            f"💤 **{interaction.user.display_name}** is now Away (Mode: `{mode.value}`).\n"
            f"Mentions will be suppressed. Use `/back` to return and get a summary.",
            ephemeral=False 
        )
    else:
        await interaction.response.send_message("❌ Failed to set away status.", ephemeral=True)

@tree.command(name="back", description="Return from away status and get a catch-up summary.")
async def back_command(interaction: discord.Interaction):
    """Returns the player to active status and provides a summary."""
    user_id = str(interaction.user.id)
    
    if not away_manager.is_away(user_id):
        await interaction.response.send_message("You are not currently marked as Away.", ephemeral=True)
        return

    away_data = away_manager.return_user(user_id)
    last_seen_id = away_data.get("last_seen_message_id", 0)
    
    await interaction.response.defer(ephemeral=True)
    
    # 1. Fetch missed messages
    summary_text = "*No significant events detected.*"
    
    try:
        missed_messages = []
        if interaction.channel:
            # We need to find the message object to use 'after'
            # If the specific ID is too old or not found, we might need a fallback.
            # discord.py's history 'after' handles an Object with an id.
            limit = 100 # Reasonable limit for summary
            
            # Since fetching by ID directly isn't easy without a message object, 
            # we create a dummy object.
            last_msg_obj = discord.Object(id=last_seen_id)
            
            async for msg in interaction.channel.history(limit=limit, after=last_msg_obj):
                if msg.author == client_discord.user and "MEMORY_UPDATE" in msg.content:
                    # Prioritize Memory updates for summary
                    missed_messages.append(f"GM Update: {msg.content}")
                elif msg.author != client_discord.user:
                     missed_messages.append(f"{msg.author.display_name}: {msg.content}")
        
        if missed_messages:
            history_block = "\n".join(missed_messages[-50:]) # Send last 50 prompts
            
            # 2. Generate Summary using AI
            # We use a quick prompt to the model
            prompt = """
            # TASK: Catch-Up Summary
            A player ({user_display_name}) has returned after being away.
            Summarize the following recent events for them in 3-4 bullet points. Focus on what their character needs to know.
            
            # RECENT SCENE LOG:
            {log_history_block}
            """.format(user_display_name=interaction.user.display_name, log_history_block=history_block)
            
            response = await client_genai.aio.models.generate_content(
                model=AI_MODEL,
                contents=prompt
            )
            
            if response.text:
                summary_text = response.text
                
    except Exception as e:
        print(f"❌ Error generating back summary: {e}")
        summary_text = f"*(System Error generating summary: {e})*"

    await interaction.followup.send(
        f"👋 Welcome back, **{interaction.user.display_name}**!\n\n**📝 Catch-Up Summary:**\n{summary_text}",
        ephemeral=True
    )
    
    # Announce publicly (optional, sticking to spec: "gm should provide them... narrative summary")
    # The spec implies the summary is for the player.
    # We also want to announce they are back to the group.
    await interaction.channel.send(f"🟢 **{interaction.user.display_name}** has returned.")

@tree.command(name="help", description="Shows a list of all available commands.")
async def help_command(interaction: discord.Interaction):
    """Shows a list of all available commands."""
    
    help_text = "Could not find the help file."
    help_file_path = pathlib.Path("personas/help_text.md")
    if help_file_path.exists():
        help_text = help_file_path.read_text(encoding="utf-8")
    
    embed = discord.Embed(
        title="📜 Command List",
        description=help_text,
        color=discord.Color.blue()
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="sheet", description="View your character sheet or another player's.")
async def sheet_command(interaction: discord.Interaction, user: Optional[discord.User] = None):
    """Displays a character sheet."""
    target_user = user if user else interaction.user
    
    character_name = get_character_name(str(target_user.id), target_user.name)
    
    if not character_name:
        await interaction.response.send_message("Could not determine character name.", ephemeral=True)
        return

    sheet_data_block = fetch_character_sheet(character_name)
    
    if not sheet_data_block:
        await interaction.response.send_message(f"Could not find a character sheet for **{character_name}**.", ephemeral=True)
        return

    data_table_pattern = r"```DATA_TABLE\s*(.*?)"
    match = re.search(data_table_pattern, sheet_data_block, re.DOTALL | re.IGNORECASE)
    
    if match:
        formatted_sheet = render_table_as_ascii(match)
        await interaction.response.send_message(formatted_sheet)
    else:
        await interaction.response.send_message(f"Found sheet data for **{character_name}**, but failed to format it.")

@tree.command(name="ledger", description="Display the master campaign ledger.")
async def ledger_command(interaction: discord.Interaction):
    """Displays the master campaign ledger."""
    
    ledger_content = load_memory()
    
    if not ledger_content:
        await interaction.response.send_message("The campaign ledger is currently empty.", ephemeral=True)
        return
        
    if len(ledger_content) > 1990:
        ledger_file = io.BytesIO(ledger_content.encode('utf-8'))
        await interaction.response.send_message(
            "The ledger is too large to display. Sending as a file.",
            file=discord.File(ledger_file, filename="campaign_ledger.md")
        )
    else:
        await interaction.response.send_message(f"```markdown\n{ledger_content}\n```")

@tree.command(name="visual", description="Request a visual for the current scene or a prompt.")
async def visual_command(interaction: discord.Interaction, prompt: Optional[str] = None):
    """Requests a visual to be generated by the AI creative director."""
    
    await interaction.response.send_message("✨ Your request has been sent to the AI Creative Director.", ephemeral=True)
    
    user_id = interaction.user.id
    
    if prompt:
        system_event_message = (
            f"[System Event: Player <@{user_id}> has requested a visual of \"{prompt}\". "
            "Generate a VISUAL_PROMPT block based on this, enriched with the current scene's context and our established art style.]"
        )
    else:
        system_event_message = (
            f"[System Event: Player <@{user_id}> has requested a visual of the current scene. "
            "Generate a VISUAL_PROMPT block capturing the most recent dramatic moment, enriched with context and style.]"
        )
        
    await interaction.channel.send(system_event_message)

@tree.command(name="ooc", description="Send an Out-of-Character message.")
async def ooc_command(interaction: discord.Interaction, message: str):
    """Sends an Out-of-Character message."""
    
    await interaction.response.send_message("Your OOC message has been sent.", ephemeral=True)
    
    formatted_message = f"[OOC] {interaction.user.display_name}: {message}"
    
    await interaction.channel.send(formatted_message)

@tree.command(name="rewind", description="Rewind the last narrative action to choose a different path.")
async def rewind_command(interaction: discord.Interaction, new_direction: str):
    """Rewinds the last narrative action."""
    await interaction.response.defer(ephemeral=True)

    last_bot_message = None
    async for msg in interaction.channel.history(limit=50):
        if msg.author == client_discord.user and not msg.content.startswith("[System Event:"):
            last_bot_message = msg
            break
            
    if not last_bot_message:
        await interaction.followup.send("Could not find a recent GM narrative to rewind.", ephemeral=True)
        return
        
    memory_update_pattern = r"```MEMORY_UPDATE\s*(.*?)"
    memory_match = re.search(memory_update_pattern, last_bot_message.content, re.DOTALL | re.IGNORECASE)
    if memory_match:
        facts_to_reverse = memory_match.group(1).strip()
        if facts_to_reverse:
            await reverse_ledgers_logic(facts_to_reverse)
            
    system_event_message = (
        f"[System Event: Rewind requested by {interaction.user.display_name}. "
        f"Disregard the previous GM message. The new direction is: \"{new_direction}\"]"
    )
    await interaction.channel.send(system_event_message)
    
    await interaction.followup.send("↩️ The narrative has been rewound.", ephemeral=True)
    try:
        await last_bot_message.add_reaction("↩️")
    except discord.HTTPException:
        pass

class ConfirmView(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=120)
        self.value = None
        self.author = author

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("You cannot interact with another user's confirmation.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Confirm Reset", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        button.disabled = True
        self.value = True
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        button.disabled = True
        self.value = False
        self.stop()


@tree.command(name="reset_memory", description="[Admin] Rebuilds campaign memory from channel history.")
@discord.app_commands.checks.has_permissions(administrator=True)
async def reset_memory_command(interaction: discord.Interaction):
    """Rebuilds campaign memory from channel history."""
    
    view = ConfirmView(interaction.user)
    await interaction.response.send_message(
        "⚠️ **WARNING**: This will wipe all current memory (.ledger files) and rebuild them from channel history. This can take 1-2 minutes. Are you sure?",
        view=view,
        ephemeral=True
    )
    
    await view.wait()
    
    if view.value is True:
        await interaction.edit_original_response(content="🔄 **Memory Reconstruction Started...** Analyzing history.", view=None)
        try:
            history_messages = [msg async for msg in interaction.channel.history(limit=500)]
            history_messages.reverse()
            
            history_text = ""
            for msg in history_messages:
                name = msg.author.name
                content = msg.content if msg.content else "[Image/Other]"
                history_text += f"{name}: {content}\n"
            
            architect_persona_path = pathlib.Path("personas/memory_architect_persona.md")
            if not architect_persona_path.exists():
                await interaction.channel.send("❌ Error: Memory Architect persona missing.")
                return
            persona_content = architect_persona_path.read_text(encoding="utf-8")
            
            prompt = f"# FULL CHANNEL HISTORY RECONSTRUCTION\n\n{history_text}\n\nBuild a fresh set of campaign ledgers based on this history."
            
            memory_dir = pathlib.Path("./memory")
            for f in memory_dir.glob("*.ledger"):
                f.unlink()
                
            response = await client_genai.aio.models.generate_content(
                model=AI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=persona_content,
                    temperature=0.1
                )
            )
            
            if response.text:
                count = save_ledger_files(response.text)
                await interaction.channel.send(f"✅ **Memory Rebuilt.** Created/Updated {count} ledgers. Use `/ledger` or `/sheet` to verify.")
            else:
                await interaction.channel.send("❌ Error: Memory Architect returned no data.")
                
        except Exception as e:
            await interaction.channel.send(f"❌ Error during reset: {e}")
    else:
        await interaction.edit_original_response(content="⏳ Reset cancelled.", view=None)

@tree.command(name="x", description="Use the X-Card safety tool to pivot the scene.")
async def x_card_command(interaction: discord.Interaction, reason: Optional[str] = None):
    """Handles the X-Card safety tool."""
    
    await interaction.response.send_message("Acknowledged. Pivoting the scene.", ephemeral=True)
    
    last_bot_message = None
    async for msg in interaction.channel.history(limit=50):
        if msg.author == client_discord.user and not msg.content.startswith("[System Event:"):
            last_bot_message = msg
            break
            
    if not last_bot_message:
        await interaction.followup.send("Could not find a recent GM narrative to rewind.", ephemeral=True)
        return
        
    memory_update_pattern = r"```MEMORY_UPDATE\s*(.*?)"
    memory_match = re.search(memory_update_pattern, last_bot_message.content, re.DOTALL | re.IGNORECASE)
    if memory_match:
        facts_to_reverse = memory_match.group(1).strip()
        if facts_to_reverse:
            await reverse_ledgers_logic(facts_to_reverse)

    await interaction.channel.send("Let's pause here and shift the focus. The scene changes...")
    
    system_event_message = (
        f"[System Event: The X-Card safety tool was used by {interaction.user.display_name}. "
        "Disregard the previous topic completely and pivot the narrative to a different scene or focus. "
        "Do not refer to the uncomfortable content again."
    )
    if reason:
        system_event_message += f" Provided reason: \"{reason}\""
        
    await interaction.channel.send(system_event_message)

def run_terminal_mode():
    """Runs the bot in an interactive terminal loop."""
    print(f"🎮 Terminal Mode: {AI_MODEL}")
    print(f"📖 Persona: {PERSONA_FILE}")
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
                    parts=[types.Part(text="*(Acknowledging history context...)*")]
                ))

            # 2. Create Chat Session
            chat = client_genai.aio.chats.create(
                model=AI_MODEL,
                config=types.GenerateContentConfig(
                    system_instruction=FULL_SYSTEM_INSTRUCTION,
                    safety_settings=safety_settings
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
    
    # Sync slash commands
    try:
        await tree.sync()
        print('✅ Slash commands synced')
    except Exception as e:
        print(f'⚠️ Failed to sync slash commands: {e}')

@client_discord.event
async def on_message(message):
    if message.author == client_discord.user:
        return
    if message.channel.id != TARGET_CHANNEL_ID:
        return

    async with message.channel.typing():
        try:
            # Context Continuity: Fetch history
            is_rewind_event = message.content.startswith("[System Event: Rewind")
            history_limit = 15
            history_messages = [msg async for msg in message.channel.history(limit=history_limit, before=message)]

            if is_rewind_event and history_messages:
                # If this is a rewind, the message just before this one is the System Event from the /rewind command.
                # The message before THAT is the GM message we need to ignore.
                # The history is returned newest-to-oldest, so we check the first element.
                if history_messages[0].author == client_discord.user:
                    history_messages.pop(0)

            history_messages.reverse()
            
            gemini_history = []
            
            for msg in history_messages:
                content_text = msg.content if msg.content else "[Action/Image]"
                
                # Determine Role and Identity
                is_bot = (msg.author == client_discord.user)
                role = "model" if is_bot else "user"
                
                # Format text with the required @Username mapping
                if not is_bot:
                    formatted_text = f"User [Name: @{message.author.name}, ID: <@{message.author.id}>]: {content_text}"
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
                    # Inject Persistent Memory into System Context
                    memory_context = load_memory()
                    
                    # Inject Away Status
                    away_users = away_manager.get_all_away_users()
                    away_block = ""
                    if away_users:
                        away_block = "\n# AWAY MODE STATUS (DO NOT TAG THESE USERS)\n"
                        for uid, data in away_users.items():
                            uname = f"<@{uid}>" # We don't have the username easily here without fetching, using ID
                            # Ideally we map ID to name, but for now ID is safer for suppression instructions
                            away_block += f"- User {uname} is AWAY. Mode: {data['mode']}.\n"
                        away_block += "INSTRUCTION: Respect the mode. If 'Auto-Pilot', you play them. If 'Narrative Exit', they are gone. NEVER mention/tag away users directly.\n"

                    dynamic_system_instruction = f"{FULL_SYSTEM_INSTRUCTION}\n\n# CAMPAIGN PERSISTENT MEMORY\n{memory_context}\n{away_block}"

                    # Async RAG Chat
                    chat = client_genai.aio.chats.create(
                        model=current_model,
                        config=types.GenerateContentConfig(
                            system_instruction=dynamic_system_instruction,
                            safety_settings=safety_settings
                        ),
                        history=gemini_history
                    )

                    # Username Injection & Generation (Awaited)
                    response = await chat.send_message(f"User [Name: @{message.author.name}, ID: <@{message.author.id}>]: {message.content}")
                    
                    if response.text:
                        res_text = response.text
                        
                        # -------------------------------------------------------------
                        # Response Processing (Refactored)
                        # -------------------------------------------------------------
                        res_text, facts_to_remember, prompt_text = process_response_formatting(res_text)

                        if facts_to_remember:
                            await update_ledgers_logic(facts_to_remember)

                        generated_file = None
                        if prompt_text:
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

                            try:
                                # Async Nano Banana Image Generation
                                img_response = await client_genai.aio.models.generate_content(
                                    model="gemini-2.5-flash-image",
                                    contents=prompt_text
                                )
                                
                                if hasattr(img_response, 'generated_images') and img_response.generated_images:
                                    image_bytes = img_response.generated_images[0].image.image_bytes
                                    generated_file = discord.File(io.BytesIO(image_bytes), filename="visual.png")
                                elif img_response.candidates and img_response.candidates[0].content.parts:
                                    # Fallback for standard multimodal response
                                    part = img_response.candidates[0].content.parts[0]
                                    if part.inline_data:
                                        generated_file = discord.File(io.BytesIO(part.inline_data.data), filename="visual.png")
                                
                                if not generated_file:
                                    finish_reason = "Unknown"
                                    if img_response.candidates:
                                        finish_reason = img_response.candidates[0].finish_reason
                                    res_text += f"\n\n*The mists of the Spire obscure your vision... (Image failed: {finish_reason})*"
                            except Exception as e:
                                err_str = str(e)
                                if "SAFETY" in err_str.upper():
                                    err_str = "Safety block triggered (Prompt violates visual safety policies)"
                                print(f"❌ Image Generation Failed: {e}")
                                res_text += f"\n\n*The mists of the Spire obscure your vision... (Technical Error: {err_str})*"

                        # -------------------------------------------------------------
                        # SILENCE_SIGNAL Interceptor
                        # -------------------------------------------------------------
                        if "[SIGNAL: SILENCE]" in res_text:
                            print(f"🤫 Bot is observing. Signal detected from {current_model}.")
                            break # Exit the retry loop and do not send any message
                        
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
    # Initialize Context and instruction only when running
    FULL_SYSTEM_INSTRUCTION = load_full_context()
    
    if "--terminal" in sys.argv:
        run_terminal_mode()
    else:
        client_discord.run(DISCORD_TOKEN)

def _syntax_check():
    """A simple function to confirm the file is syntactically correct."""
    return True
