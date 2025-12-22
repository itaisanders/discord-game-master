
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from bot import on_message

@pytest.mark.asyncio
async def test_reset_memory_command_cancel():
    """Test that /reset_memory cancels if 'yes' is not typed."""
    message = AsyncMock()
    message.channel.id = 123
    message.content = "/reset_memory"
    message.author.name = "TestUser"
    
    # Mock global TARGET_CHANNEL_ID
    with patch("bot.TARGET_CHANNEL_ID", 123):
        with patch("bot.client_discord.wait_for", side_effect=asyncio.TimeoutError):
            await on_message(message)
            
    # Check if warning was sent and then timeout message
    message.channel.send.assert_any_call("⏳ Reset cancelled (Timeout).")

@pytest.mark.asyncio
async def test_reset_memory_command_success():
    """Test that /reset_memory proceed if 'yes' is typed."""
    message = AsyncMock()
    message.channel.id = 123
    message.content = "/reset_memory"
    message.author.name = "TestUser"
    
    # Mock confirmation message
    confirm_msg = MagicMock()
    confirm_msg.author = message.author
    confirm_msg.content = "yes"
    
    # Mock history
    mock_msg = MagicMock()
    mock_msg.author.name = "User"
    mock_msg.content = "Hello history"
    
    async def mock_history(limit):
        yield mock_msg

    message.channel.history = MagicMock(side_effect=mock_history)

    # Mock Gemini call
    mock_res = MagicMock()
    mock_res.text = "```FILE: rebuilt.ledger\nContent```"
    
    with patch("bot.TARGET_CHANNEL_ID", 123):
        with patch("bot.client_discord.wait_for", new_callable=AsyncMock) as mock_wait:
            mock_wait.return_value = confirm_msg
            with patch("bot.client_genai.models.generate_content", return_value=mock_res):
                with patch("bot.pathlib.Path") as mock_path:
                    mock_path.return_value.glob.return_value = [] # no old files
                    mock_path.return_value.exists.return_value = True
                    mock_path.return_value.read_text.return_value = "Persona content"
                    
                    await on_message(message)

    # Check for success message
    message.channel.send.assert_any_call("✅ **Memory Rebuilt.** Created/Updated 1 ledgers. Use `/ledger` or `/sheet` to verify.")

@pytest.mark.asyncio
async def test_on_message_ignores_other_channels():
    """Test that the bot ignores messages not in the target channel."""
    message = AsyncMock()
    message.channel.id = 999 # Wrong channel
    
    with patch("bot.TARGET_CHANNEL_ID", 123):
        await on_message(message)
    
    # Should not have called typing() or sent any messages
    assert not message.channel.typing.called
