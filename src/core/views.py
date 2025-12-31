
import discord

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

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
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


class FeedbackConfirmView(discord.ui.View):
    def __init__(self, author, feedback_type: str, original_message: str, interpretation: str, channel, on_confirm_callback):
        super().__init__(timeout=300)
        self.value = None
        self.author = author
        self.feedback_type = feedback_type
        self.original_message = original_message
        self.interpretation = interpretation
        self.channel = channel
        self.on_confirm_callback = on_confirm_callback

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("You cannot interact with another user's feedback confirmation.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Confirm & Save", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Call the callback to record feedback
        await self.on_confirm_callback(self.feedback_type, self.author.name, self.original_message, self.interpretation)
        
        self.value = True
        self.stop()
        button.disabled = True
        
        # Public confirmation message
        feedback_summary = self.interpretation.split('```')[0].strip()
        if len(feedback_summary) > 280:
             feedback_summary = feedback_summary[:280] + "..."

        icon = "⭐" if self.feedback_type == "star" else "🙏"
        public_message = f"{icon} The GM has noted a new '{self.feedback_type.capitalize()}' from a player: *\"{feedback_summary}\"*"
        
        await self.channel.send(public_message)
        await interaction.response.edit_message(content="✅ Got it. Your feedback has been recorded and shared with the party.", view=None)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()
        button.disabled = True
        await interaction.response.edit_message(content="Feedback cancelled.", view=None)
