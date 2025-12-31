
import sys
import os
import asyncio
import io
import re
import pathlib
import discord
from typing import Optional
from google import genai
from google.genai import types

# Add the project root to sys.path so we can import src modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.config import validate_config, DISCORD_TOKEN, AI_MODEL, TARGET_CHANNEL_ID, PERSONA_FILE
from src.core.client import client_discord, tree, client_genai

# Import Modules
from src.modules.dice.rolling import roll
from src.modules.presence.manager import AwayManager
from src.modules.memory.service import (
    load_full_context, 
    update_ledgers_logic, 
    reverse_ledgers_logic, 
    load_memory, 
    get_character_name, 
    fetch_character_sheet,
    get_feedback_interpretation,
    record_feedback,
    save_ledger_files
)
from src.modules.narrative.parser import (
    process_response_formatting, 
    pending_rolls, 
    filter_away_mentions
)

from src.core.views import ConfirmView, FeedbackConfirmView

# Initialize Managers
away_manager = AwayManager() 

# ------------------------------------------------------------------
# EVENT HANDLERS
# ------------------------------------------------------------------

@client_discord.event
async def on_ready():
    print(f'✅ Logged in as {client_discord.user} (ID: {client_discord.user.id})')
    print(f'🎯 Listening on Channel ID: {TARGET_CHANNEL_ID}')
    
    # Sync Slash Commands
    try:
        synced = await tree.sync()
        print(f"🔄 Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"❌ Failed to sync slash commands: {e}")

    # Load Context
    print("🧠 Loading Campaign Context...")
    full_context = load_full_context()
    print(f"✨ System Instruction Loaded ({len(full_context)} chars).")

@client_discord.event
async def on_message(message):
    if message.author == client_discord.user:
        return

    # Only process target channel
    if TARGET_CHANNEL_ID and message.channel.id != TARGET_CHANNEL_ID:
        return

    # Ignore generic "commands" (legacy text commands)
    if message.content.startswith('/'):
        return

    # --- MAIN AI NARRATIVE LOOP ---
    if message.content.strip().startswith("(") or message.content.strip().startswith("[OOC]"):
        return 

    async with message.channel.typing():
        try:
            full_context = load_full_context()
            ledger_content = load_memory()
            
            history = []
            async for msg in message.channel.history(limit=15):
                role = "model" if msg.author == client_discord.user else "user"
                content = msg.content
                if role == "user":
                    content = f"{msg.author.display_name}: {content}"
                history.append(types.Content(role=role, parts=[types.Part.from_text(text=content)]))
            
            history.reverse()
            final_system_instruction = f"{full_context}\n\n# CURRENT CAMPAIGN STATE (READ-ONLY)\n{ledger_content}"
            
            response = await client_genai.aio.models.generate_content(
                model=AI_MODEL,
                contents=history,
                config=types.GenerateContentConfig(
                    system_instruction=final_system_instruction,
                    temperature=0.7
                )
            )
            
            if response.text:
                final_text, facts, visual_prompt = process_response_formatting(response.text)
                
                # Simple Smart Chunking
                chunks = [final_text[i:i+1950] for i in range(0, len(final_text), 1950)]
                for chunk in chunks:
                    if chunk.strip():
                        await message.channel.send(chunk)

                if facts:
                    await update_ledgers_logic(facts)
                if visual_prompt:
                    # Logic for visual prompt system event
                    await message.channel.send(f"[System Event: Visual Prompt triggered: {visual_prompt}]")
        except Exception as e:
            print(f"❌ Error in message loop: {e}")


# ------------------------------------------------------------------
# COMMAND HANDLERS
# ------------------------------------------------------------------

@tree.command(name="roll", description="Roll dice (e.g., 2d6+3) or execute pending roll")
async def roll_command(interaction: discord.Interaction, dice: Optional[str] = None):
    if dice is None:
        username = interaction.user.name
        if username in pending_rolls:
            pending = pending_rolls[username]
            result = roll(pending["notation"])
            if result.error:
                await interaction.response.send_message(f"❌ Invalid pending roll: {result.error}", ephemeral=True)
            else:
                del pending_rolls[username]
                await interaction.response.send_message(f"🎲 **{interaction.user.display_name}** rolls {pending['notation']} for {pending['reason']}: {result.formatted}")
        else:
            await interaction.response.send_message("❌ No pending roll found.", ephemeral=True)
        return

    result = roll(dice)
    if result.error:
        await interaction.response.send_message(f"❌ Invalid dice notation: {result.error}", ephemeral=True)
    else:
        await interaction.response.send_message(f"🎲 **{interaction.user.display_name}** rolls {dice}: {result.formatted}")

@tree.command(name="sheet", description="View your character sheet or another player's.")
async def sheet_command(interaction: discord.Interaction, user: Optional[discord.User] = None):
    await interaction.response.defer(ephemeral=True)
    target = user if user else interaction.user
    name = get_character_name(str(target.id), target.name)
    if not name:
        await interaction.followup.send("Character not found in ledger.", ephemeral=True)
        return
    sheet = await fetch_character_sheet(name)
    if sheet:
        await interaction.followup.send(f"```markdown\n{sheet[:1900]}\n```", ephemeral=True)
    else:
        await interaction.followup.send(f"Sheet for {name} not found.", ephemeral=True)

@tree.command(name="ledger", description="View master ledger.")
async def ledger_command(interaction: discord.Interaction):
    content = load_memory()
    if len(content) > 1900:
        f = io.BytesIO(content.encode('utf-8'))
        await interaction.response.send_message("Ledger file:", file=discord.File(f, "ledger.md"), ephemeral=True)
    else:
        await interaction.response.send_message(f"```markdown\n{content}\n```", ephemeral=True)

@tree.command(name="help", description="Shows a list of all available commands.")
async def help_command(interaction: discord.Interaction):
    help_text = "Could not find the help file."
    help_file_path = pathlib.Path("personas/help_text.md")
    if help_file_path.exists():
        help_text = help_file_path.read_text(encoding="utf-8")
    embed = discord.Embed(title="📜 Command List", description=help_text, color=discord.Color.blue())
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="away", description="Mark yourself as away.")
@discord.app_commands.choices(mode=[
    discord.app_commands.Choice(name="Auto-Pilot", value="auto-pilot"),
    discord.app_commands.Choice(name="Off-Screen", value="off-screen"),
    discord.app_commands.Choice(name="Narrative Exit", value="narrative-exit")
])
async def away_command(interaction: discord.Interaction, mode: discord.app_commands.Choice[str]):
    last_msg_id = interaction.channel.last_message_id if interaction.channel else 0
    success = away_manager.set_away(str(interaction.user.id), mode.value, last_msg_id or 0)
    if success:
        await interaction.response.send_message(f"💤 **{interaction.user.display_name}** is now Away ({mode.value}).", ephemeral=False)
    else:
        await interaction.response.send_message("❌ Failed.", ephemeral=True)

@tree.command(name="back", description="Return from away.")
async def back_command(interaction: discord.Interaction):
    if not away_manager.is_away(str(interaction.user.id)):
        await interaction.response.send_message("You are not away.", ephemeral=True)
        return
    away_manager.return_user(str(interaction.user.id))
    await interaction.response.send_message(f"👋 Welcome back **{interaction.user.display_name}**!", ephemeral=True)
    await interaction.channel.send(f"🟢 **{interaction.user.display_name}** has returned.")

@tree.command(name="ooc", description="Send an Out-of-Character message.")
async def ooc_command(interaction: discord.Interaction, message: str):
    await interaction.response.send_message("Sent.", ephemeral=True)
    await interaction.channel.send(f"[OOC] {interaction.user.display_name}: {message}")

@tree.command(name="visual", description="Request a visual for the current scene.")
async def visual_command(interaction: discord.Interaction, prompt: Optional[str] = None):
    await interaction.response.send_message("✨ Request sent.", ephemeral=True)
    msg = f"[System Event: Player <@{interaction.user.id}> requested visual of \"{prompt}\".]" if prompt else f"[System Event: Player <@{interaction.user.id}> requested scene visual.]"
    await interaction.channel.send(msg)

@tree.command(name="rewind", description="Rewind the last GM action.")
async def rewind_command(interaction: discord.Interaction, new_direction: str):
    await interaction.response.defer(ephemeral=True)
    last_bot_msg = None
    async for msg in interaction.channel.history(limit=50):
        if msg.author == client_discord.user and not msg.content.startswith("[System Event:"):
            last_bot_msg = msg
            break
    if not last_bot_msg:
        await interaction.followup.send("No recent GM narrative found.", ephemeral=True)
        return
    
    memory_match = re.search(r"```MEMORY_UPDATE\s*(.*?)", last_bot_msg.content, re.DOTALL | re.IGNORECASE)
    if memory_match and memory_match.group(1).strip():
        await reverse_ledgers_logic(memory_match.group(1).strip())
    
    await interaction.channel.send(f"[System Event: Rewind requested by {interaction.user.display_name}. New direction: \"{new_direction}\"]")
    await interaction.followup.send("↩️ Rewound.", ephemeral=True)

@tree.command(name="x", description="Use the X-Card safety tool.")
async def x_command(interaction: discord.Interaction, reason: Optional[str] = None):
    await interaction.response.send_message("Safety tool activated. Pivoting.", ephemeral=True)
    await interaction.channel.send("Let's pause here and shift focus.")
    msg = f"[System Event: X-Card used by {interaction.user.display_name}. Reason: {reason}]" if reason else f"[System Event: X-Card used by {interaction.user.display_name}.]"
    await interaction.channel.send(msg)

@tree.command(name="stars", description="Feedback: Something you liked.")
async def stars_command(interaction: discord.Interaction, message: str):
    await interaction.response.defer(ephemeral=True, thinking=True)
    interpretation = await get_feedback_interpretation("star", message)
    view = FeedbackConfirmView(interaction.user, "star", message, interpretation, interaction.channel, record_feedback)
    await interaction.followup.send(f"### ⭐ Interpretation:\n> {interpretation}\n\nConfirm?", view=view, ephemeral=True)

@tree.command(name="wishes", description="Feedback: Something you want to see.")
async def wishes_command(interaction: discord.Interaction, message: str):
    await interaction.response.defer(ephemeral=True, thinking=True)
    interpretation = await get_feedback_interpretation("wish", message)
    view = FeedbackConfirmView(interaction.user, "wish", message, interpretation, interaction.channel, record_feedback)
    await interaction.followup.send(f"### 🙏 Interpretation:\n> {interpretation}\n\nConfirm?", view=view, ephemeral=True)

@tree.command(name="reset_memory", description="[Admin] Rebuild memory from history.")
@discord.app_commands.checks.has_permissions(administrator=True)
async def reset_memory_command(interaction: discord.Interaction):
    view = ConfirmView(interaction.user)
    await interaction.response.send_message("⚠️ Wipe and rebuild all ledgers?", view=view, ephemeral=True)
    await view.wait()
    if view.value:
        await interaction.edit_original_response(content="🔄 Rebuilding...", view=None)
        # Simplified reconstruction logic
        history_messages = [msg async for msg in interaction.channel.history(limit=500)]
        history_messages.reverse()
        history_text = "\n".join([f"{m.author.name}: {m.content}" for m in history_messages])
        
        architect_persona_path = pathlib.Path("personas/memory_architect_persona.md")
        persona_content = architect_persona_path.read_text(encoding="utf-8")
        
        response = await client_genai.aio.models.generate_content(
            model=AI_MODEL,
            contents=f"# HISTORY\n{history_text}\n\nBuild fresh ledgers.",
            config=types.GenerateContentConfig(system_instruction=persona_content, temperature=0.1)
        )
        if response.text:
            count = save_ledger_files(response.text)
            await interaction.channel.send(f"✅ Memory Rebuilt ({count} files).")
    else:
        await interaction.edit_original_response(content="Cancelled.", view=None)


# ------------------------------------------------------------------
# TERMINAL MODE
# ------------------------------------------------------------------

def run_terminal_mode():
    """Runs the bot in an interactive terminal loop."""
    print(f"🎮 Terminal Mode: {AI_MODEL}")
    print(f"📖 Persona: {PERSONA_FILE}")
    print("--------------------------------------------------")
    print("Type your message to interact. Type 'exit' to quit.")
    print("--------------------------------------------------")

    local_history = []
    # Load context once
    full_instruction = load_full_context()
    
    # Standard safety settings for terminal
    safety_settings = [
        types.SafetySetting(
            category="HARM_CATEGORY_HARASSMENT",
            threshold="BLOCK_NONE"
        ),
        types.SafetySetting(
            category="HARM_CATEGORY_HATE_SPEECH",
            threshold="BLOCK_NONE"
        ),
        types.SafetySetting(
            category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
            threshold="BLOCK_NONE"
        ),
        types.SafetySetting(
            category="HARM_CATEGORY_DANGEROUS_CONTENT",
            threshold="BLOCK_NONE"
        ),
    ]

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
            # 1. Format history
            gemini_history = []
            for role, text in local_history:
                if gemini_history and gemini_history[-1].role == role:
                     gemini_history[-1].parts[0].text += "\n" + text
                else:
                    gemini_history.append(types.Content(role=role, parts=[types.Part.from_text(text=text)]))

            # Maintain alternation
            if gemini_history and gemini_history[-1].role == "user":
                 gemini_history.append(types.Content(
                    role="model",
                    parts=[types.Part.from_text(text="*(Acknowledging history context...)*")]
                ))

            # 2. Create Chat Session
            chat = client_genai.aio.chats.create(
                model=AI_MODEL,
                config=types.GenerateContentConfig(
                    system_instruction=full_instruction,
                    safety_settings=safety_settings
                ),
                history=gemini_history
            )

            # 3. Send Message (Synchronously wait for async in terminal? No, we need asyncio run or just use sync client?)
            # client_genai.aio is async. We need to run it in event loop.
            # Simplified: Just run the coroutine.
            
            async def send_to_gemini():
                formatted_input = f"User [@Terminal]: {user_input}"
                response = await chat.send_message(formatted_input)
                return response.text, formatted_input

            response_text, formatted_input = asyncio.run(send_to_gemini())
            
            if response_text:
                print(" " * 20, end="\r")
                print(f"{response_text}")
                local_history.append(("user", formatted_input))
                local_history.append(("model", response_text))
            else:
                print("\n(No text response)")

        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    if not validate_config():
        print("❌ Error: Missing environment variables.")
        exit(1)
        
    if "--terminal" in sys.argv:
        run_terminal_mode()
    else:
        print("🚀 Starting Game Master Bot (Full Architecture)...")
        client_discord.run(DISCORD_TOKEN)
