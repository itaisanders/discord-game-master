import discord
from discord import app_commands
import io
import pathlib
from .manager import BardManager
from .scriptwriter import Scriptwriter
from src.core.tts import TTSProvider
from src.modules.memory.service import load_memory
from prettytable import PrettyTable

class BardCommands:
    def __init__(self, tree: app_commands.CommandTree, bard_manager: BardManager, tts_provider: TTSProvider):
        self.tree = tree
        self.bard_manager = bard_manager
        self.scriptwriter = Scriptwriter()
        self.tts_provider = tts_provider
        
        if self.bard_manager.is_configured():
            self._register_commands()

    def _register_commands(self):
        @self.tree.command(name="summary", description="Generate a cinematic vocal recap of the story.")
        @app_commands.choices(scope=[
            app_commands.Choice(name="Current Session", value="session"),
            app_commands.Choice(name="Campaign Overview", value="campaign")
        ])
        async def summary(interaction: discord.Interaction, scope: str = "session"):
            await interaction.response.defer(ephemeral=False)
            
            try:
                # 1. Gather History/Context
                # Simplified: fetch last 25 messages for session summary
                history_msgs = []
                async for msg in interaction.channel.history(limit=25):
                    if msg.author.bot and not msg.content.startswith("🎲"):
                        # Keep bot narrative, ignore dice blocks/commands
                        history_msgs.append(f"GM: {msg.content}")
                    elif not msg.author.bot:
                        history_msgs.append(f"{msg.author.display_name}: {msg.content}")
                
                history_msgs.reverse()
                history_text = "\n".join(history_msgs)
                ledger_context = load_memory()
                
                # 2. Generate Script
                await interaction.edit_original_response(content="✍️ **The Bard is writing the script...**")
                script = await self.scriptwriter.generate_script(history_text, ledger_context)
                
                # 3. Perform Audio
                try:
                    await interaction.edit_original_response(content="🎙️ **The Narrator is performing...**")
                    voice_def = self.bard_manager.get_selected_voice()
                    audio_data = await self.tts_provider.generate_audio(script, voice_def['provider_id'])
                    
                    # 4. Send File
                    audio_data.seek(0)
                    discord_file = discord.File(fp=audio_data, filename="recap.mp3")
                    
                    await interaction.edit_original_response(
                        content=f"📖 **Cinematic Recap** (Narrated by: {voice_def['name']})\n||{script[:1800]}...||", 
                        attachments=[discord_file]
                    )
                except Exception as tts_error:
                    print(f"⚠️ TTS Failed: {tts_error}")
                    await interaction.edit_original_response(
                        content=f"📜 **The Bard's voice is hoarse, but the scroll remains.**\n\n**Cinematic Script:**\n>>> {script}"
                    )
                
                self.bard_manager.update_summary_timestamp()
                
            except Exception as e:
                print(f"❌ Bard Error: {e}")
                await interaction.edit_original_response(content=f"❌ **The Bard's voice cracked!** (Error: {e})")

        @self.tree.command(name="voice", description="Manage the Narrator's voice.")
        async def voice_base(interaction: discord.Interaction):
            pass # Parent for subcommands

        @self.tree.command(name="voice-list", description="List available narrator voices and styles.")
        async def voice_list(interaction: discord.Interaction):
            registry = self.bard_manager.get_voice_registry()
            pt = PrettyTable()
            pt.field_names = ["Key", "Name", "Vibe/Style"]
            pt.align = "l"
            
            for key, val in registry.items():
                pt.add_row([key, val['name'], val['style']])
            
            current = self.bard_manager.selected_voice_key
            await interaction.response.send_message(
                f"🎙️ **Available Narrators**\n```text\n{pt.get_string()}\n```\n**Active:** `{current}`", 
                ephemeral=True
            )

        @self.tree.command(name="voice-set", description="Choose the narrator for your recaps.")
        async def voice_set(interaction: discord.Interaction, key: str):
            if self.bard_manager.set_selected_voice(key):
                voice = self.bard_manager.get_selected_voice()
                await interaction.response.send_message(
                    f"✅ **Narrator updated to:** {voice['name']}\n> *{voice['style']}*", 
                    ephemeral=False
                )
            else:
                await interaction.response.send_message(f"❌ Unknown voice key: `{key}`", ephemeral=True)

def register_bard_commands(tree: app_commands.CommandTree, bard_manager: BardManager, tts_provider: TTSProvider):
    return BardCommands(tree, bard_manager, tts_provider)
