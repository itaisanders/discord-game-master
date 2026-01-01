import discord
from .state import TableManager, TableState

class StateChangeView(discord.ui.View):
    def __init__(self, target_state: str, reason: str, table_manager: TableManager, original_user: discord.User):
        super().__init__(timeout=60)
        self.target_state = target_state
        self.reason = reason
        self.table_manager = table_manager
        self.original_user = original_user

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Allow any user to confirm since this is a table-wide event
        return True

    @discord.ui.button(label="✅ Confirm Change", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            # Convert string to Enum
            new_state = TableState(self.target_state.upper())
            self.table_manager.set_state(new_state)
            
            # Disable buttons
            for child in self.children:
                child.disabled = True
            
            await interaction.response.edit_message(content=f"✅ **Table State Updated** to `{new_state.value}`.\n> Reason: {self.reason}", view=self)
            
        except ValueError:
            await interaction.response.send_message(f"❌ Invalid state requested: {self.target_state}", ephemeral=True)

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content=f"🚫 State change cancelled.", view=self)
