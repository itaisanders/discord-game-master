
import os
import pytest
from dotenv import load_dotenv

@pytest.fixture
def env_vars():
    load_dotenv()
    return os.environ

def test_environment_variables(env_vars):
    """Critical: Ensure all critical environment variables are present."""
    required_vars = [
        "DISCORD_TOKEN",
        "GEMINI_API_KEY",
        "TARGET_CHANNEL_ID",
    ]
    for var in required_vars:
        assert var in env_vars, f"Missing critical environment variable: {var}"

def test_gm_persona_file_exists():
    import pathlib
    gm_persona_path = pathlib.Path("src/modules/narrative/gm_persona.md")
    assert gm_persona_path.exists(), f"GM Persona file not found at: {gm_persona_path}"

def test_pdf_directory_structure():
    """Critical: Ensure the PDF directory exists (even if empty)."""
    assert os.path.isdir("pdf"), "The 'pdf' directory is missing."



def test_scripts_directory_structure():
    """Critical: Ensure the scripts directory exists."""
    assert os.path.isdir("scripts"), "The 'scripts' directory is missing."

def test_target_channel_id_is_int(env_vars):
    """Critical: Ensure TARGET_CHANNEL_ID can be cast to an integer."""
    channel_id = env_vars.get("TARGET_CHANNEL_ID")
    assert channel_id.isdigit(), "TARGET_CHANNEL_ID must be a numeric string."

