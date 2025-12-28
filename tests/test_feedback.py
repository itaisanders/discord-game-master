import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import discord
import unittest

# Since the commands are in bot.py, we need to import them
from bot import stars_command, wishes_command, FeedbackConfirmView, record_feedback

@pytest.fixture
def mock_interaction():
    """Fixture to create a mock Discord interaction."""
    interaction = AsyncMock(spec=discord.Interaction)
    interaction.user = AsyncMock(spec=discord.User)
    interaction.user.id = 12345
    interaction.user.name = "TestUser"
    interaction.user.display_name = "TestUser"
    interaction.response = AsyncMock(spec=discord.InteractionResponse)
    interaction.followup = AsyncMock(spec=discord.Webhook)
    interaction.channel = AsyncMock(spec=discord.TextChannel)
    return interaction

@pytest.mark.asyncio
async def test_stars_command_confirm_flow(mock_interaction):
    """Test the full /stars command flow where the user confirms."""
    test_message = "I really enjoyed the fight with the dragon."
    test_interpretation = "I understand you liked the epic combat encounter."

    # We patch the two external-facing functions: the AI call and the file write.
    with patch("bot.get_feedback_interpretation", new_callable=AsyncMock, return_value=test_interpretation) as mock_get_interp, \
         patch("bot.record_feedback", new_callable=AsyncMock) as mock_record_feedback:

        # 1. Execute the slash command
        await stars_command.callback(mock_interaction, message=test_message)

        # 2. Verify the initial response and AI call
        mock_interaction.response.defer.assert_called_once_with(ephemeral=True, thinking=True)
        mock_get_interp.assert_called_once_with("star", test_message)

        # 3. Verify that the confirmation message and view were sent
        mock_interaction.followup.send.assert_called_once()
        call_args, call_kwargs = mock_interaction.followup.send.call_args
        
        sent_content = call_args[0]
        sent_view = call_kwargs['view']
        
        assert "⭐ Thank you for your feedback!" in sent_content
        assert test_message in sent_content
        assert test_interpretation in sent_content
        assert isinstance(sent_view, FeedbackConfirmView)

        # 4. Simulate the user clicking the "Confirm & Save" button
        confirm_button = next(child for child in sent_view.children if child.label == "Confirm & Save")
        
        # The button callback needs an interaction object to operate on
        button_interaction = AsyncMock(spec=discord.Interaction)
        button_interaction.response = AsyncMock(spec=discord.InteractionResponse)
        
        await confirm_button.callback(button_interaction)

        # 5. Verify that record_feedback was called with the correct arguments
        mock_record_feedback.assert_called_once_with(
            "star", 
            mock_interaction.user.name, 
            test_message, 
            test_interpretation
        )

        # 6. Verify the confirmation message was edited
        button_interaction.response.edit_message.assert_called_once_with(
            content="✅ Got it. Your feedback has been recorded and shared with the party.", 
            view=None
        )

        # 7. Verify the public message was sent to the original channel
        mock_interaction.channel.send.assert_called_once()


@pytest.mark.asyncio
async def test_wishes_command_cancel_flow(mock_interaction):
    """Test the full /wishes command flow where the user cancels."""
    test_message = "I wish we could explore the northern mountains."
    test_interpretation = "I understand you want more exploration-focused adventures."

    with patch("bot.get_feedback_interpretation", new_callable=AsyncMock, return_value=test_interpretation) as mock_get_interp, \
         patch("bot.record_feedback", new_callable=AsyncMock) as mock_record_feedback:

        # 1. Execute the slash command
        await wishes_command.callback(mock_interaction, message=test_message)

        # 2. Verify the initial response and AI call
        mock_interaction.response.defer.assert_called_once_with(ephemeral=True, thinking=True)
        mock_get_interp.assert_called_once_with("wish", test_message)

        # 3. Get the view from the followup message
        mock_interaction.followup.send.assert_called_once()
        call_args, call_kwargs = mock_interaction.followup.send.call_args
        sent_view = call_kwargs['view']
        
        # 4. Simulate the user clicking the "Cancel" button
        cancel_button = next(child for child in sent_view.children if child.label == "Cancel")
        button_interaction = AsyncMock(spec=discord.Interaction)
        button_interaction.response = AsyncMock(spec=discord.InteractionResponse)
        
        await cancel_button.callback(button_interaction)

        # 5. Verify that record_feedback was NOT called
        mock_record_feedback.assert_not_called()

        # 6. Verify the cancellation message was sent
        button_interaction.response.edit_message.assert_called_once_with(
            content="Feedback cancelled.", 
            view=None
        )

@pytest.mark.asyncio
async def test_record_feedback_parsing_and_write():
    """
    Test that record_feedback correctly parses the FEEDBACK_UPDATE block
    and writes only its content to the file.
    """
    feedback_type = "star"
    user = "TestUser"
    message = "Test message"
    
    feedback_content = "- [Fact] Player enjoyed the dragon fight."
    interpretation = (
        "I understand you liked the combat.\n"
        "```FEEDBACK_UPDATE\n"
        f"{feedback_content}\n"
        "```"
    )
    
    m = unittest.mock.mock_open()
    with patch("builtins.open", m):
        with patch("time.strftime", return_value="2025-01-01 12:00:00"):
            await record_feedback(feedback_type, user, message, interpretation)

    # Verify the file was opened in append mode
    m.assert_called_once_with(unittest.mock.ANY, "a", encoding="utf-8")
    
    # Verify the content that was written
    expected_entry = (
        f"# Entry added on 2025-01-01 12:00:00 from user TestUser\n"
        f"{feedback_content}\n\n"
    )
    
    handle = m()
    handle.write.assert_called_once_with(expected_entry)
