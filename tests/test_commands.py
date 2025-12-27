import pytest
from unittest.mock import AsyncMock, patch
import discord
from bot import help_command, sheet_command, ledger_command, ooc_command

# Since we are testing slash commands, we need to mock the Interaction object
# and its relevant properties and methods.

@pytest.fixture
def mock_interaction():
    """Fixture to create a mock Discord interaction."""
    interaction = AsyncMock(spec=discord.Interaction)
    interaction.user = AsyncMock(spec=discord.User)
    interaction.user.id = 12345
    interaction.user.name = "TestUser"
    interaction.user.display_name = "TestUser"
    interaction.channel = AsyncMock(spec=discord.TextChannel)
    interaction.response = AsyncMock(spec=discord.InteractionResponse)
    interaction.followup = AsyncMock(spec=discord.Webhook)
    return interaction

@pytest.mark.asyncio
async def test_help_command(mock_interaction):
    """Test the /help command sends an ephemeral embed."""
    await help_command.callback(mock_interaction)
    mock_interaction.response.send_message.assert_called_once()
    # Check that an embed was sent and it was ephemeral
    call_args, call_kwargs = mock_interaction.response.send_message.call_args
    assert 'embed' in call_kwargs
    assert call_kwargs['ephemeral'] is True

@pytest.mark.asyncio
async def test_ooc_command(mock_interaction):
    """Test the /ooc command sends a formatted public message."""
    test_message = "This is a test message."
    await ooc_command.callback(mock_interaction, message=test_message)
    
    # It should send an ephemeral confirmation
    mock_interaction.response.send_message.assert_called_once_with(
        "Your OOC message has been sent.", ephemeral=True
    )
    
    # And then a public, formatted message
    mock_interaction.channel.send.assert_called_once_with(
        f"[OOC] {mock_interaction.user.display_name}: {test_message}"
    )

@pytest.mark.asyncio
async def test_ledger_command_empty(mock_interaction):
    """Test the /ledger command when the ledger is empty."""
    with patch("bot.load_memory", return_value=""):
        await ledger_command.callback(mock_interaction)
        mock_interaction.response.send_message.assert_called_once_with(
            "The campaign ledger is currently empty.", ephemeral=True
        )

@pytest.mark.asyncio
async def test_ledger_command_with_content(mock_interaction):
    """Test the /ledger command with content."""
    ledger_content = "Fact 1\nFact 2"
    with patch("bot.load_memory", return_value=ledger_content):
        await ledger_command.callback(mock_interaction)
        mock_interaction.response.send_message.assert_called_once_with(
            f"```markdown\n{ledger_content}\n```"
        )

@pytest.mark.asyncio
async def test_sheet_command_not_found(mock_interaction):
    """Test /sheet command when no sheet is found for a character."""
    with patch("bot.get_character_name", return_value="TestCharacter"), \
         patch("bot.fetch_character_sheet", return_value=None):
        
        await sheet_command.callback(mock_interaction)
        
        mock_interaction.followup.send.assert_called_once_with(
            "Could not find a character sheet for **TestCharacter**.", ephemeral=True
        )

@pytest.mark.asyncio
async def test_sheet_command_found(mock_interaction):
    """Test /sheet command when a sheet is found."""
    # This is the raw markdown content that fetch_character_sheet will now return
    sheet_content = """
| Name | User | Class |
|:---|:---|:---|
| **TestCharacter** | @TestUser | Fighter |

**Abilities:**
- Power Attack
    """.strip()

    # The command will wrap this content in a markdown block
    expected_message = f"```markdown\n{sheet_content}\n```"

    with patch("bot.get_character_name", return_value="TestCharacter"), \
         patch("bot.fetch_character_sheet", return_value=sheet_content):

        await sheet_command.callback(mock_interaction)
        
        # Verify the followup message indicates success
        mock_interaction.edit_original_response.assert_called_once_with(content="Character sheet for **TestCharacter** sent!")

        # Verify the public message contains the correct sheet content
        mock_interaction.channel.send.assert_called_once_with(expected_message)
