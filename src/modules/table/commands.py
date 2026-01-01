import discord
from discord import app_commands
from .state import TableManager, TableState

def register_table_commands(tree: app_commands.CommandTree, table_manager: TableManager):
    @tree.command(name="session", description="Manage the high-level phase of the game session.")
    @app_commands.choices(state=[
        app_commands.Choice(name="Start Session (Active)", value="start"),
        app_commands.Choice(name="Session Zero (World Building)", value="zero"),
        app_commands.Choice(name="Pause Session (Bio-break)", value="pause"),
        app_commands.Choice(name="Resume Session (Back to Play)", value="resume"),
        app_commands.Choice(name="End Session (Debrief)", value="end"),
        app_commands.Choice(name="Close Table (Idle)", value="close")
    ])
    async def session_command(interaction: discord.Interaction, state: app_commands.Choice[str]):
        """Sets the table state and notifies the channel."""
        new_value = state.value
        old_state = table_manager.get_state()
        
        msg = ""
        target_state = None

        if new_value == "start":
            target_state = TableState.ACTIVE
            msg = "⚔️ **The Session Begins!** Narrative engine is now ACTIVE."
        elif new_value == "zero":
            target_state = TableState.SESSION_ZERO
            msg = "🗺️ **Session Zero Started.** Focus shifted to world-building and character creation."
        elif new_value == "pause":
            target_state = TableState.PAUSED
            msg = "⏸️ **Session Paused.** The world is frozen in place. (Narrative engine suspended)"
        elif new_value == "resume":
            target_state = TableState.ACTIVE
            msg = "▶️ **Session Resumed.** Welcome back to the story!"
        elif new_value == "end":
            target_state = TableState.DEBRIEF
            msg = "🕯️ **Session Ended.** Entering Debrief phase. Please share your `/stars` and `/wishes`!"
        elif new_value == "close":
            target_state = TableState.IDLE
            msg = "💤 **Table Closed.** The bot is now idle. See you next time!"

        if target_state:
            table_manager.set_state(target_state)
            await interaction.response.send_message(msg)
        else:
            await interaction.response.send_message("❌ Invalid session state.", ephemeral=True)
