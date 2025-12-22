
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
        "STORE_ID",
        "TARGET_CHANNEL_ID",
        "PERSONA_FILE",
        "AI_MODEL"
    ]
    for var in required_vars:
        assert var in env_vars, f"Missing critical environment variable: {var}"

def test_persona_file_exists(env_vars):
    """Critical: Ensure the persona file actually exists on disk."""
    persona_path = env_vars.get("PERSONA_FILE")
    assert persona_path is not None
    assert os.path.exists(persona_path), f"Persona file not found at: {persona_path}"

def test_pdf_directory_structure():
    """Critical: Ensure the PDF directory exists (even if empty)."""
    assert os.path.isdir("pdf"), "The 'pdf' directory is missing."

def test_personas_directory_structure():
    """Critical: Ensure the personas directory exists."""
    assert os.path.isdir("personas"), "The 'personas' directory is missing."

def test_scripts_directory_structure():
    """Critical: Ensure the scripts directory exists."""
    assert os.path.isdir("scripts"), "The 'scripts' directory is missing."

def test_target_channel_id_is_int(env_vars):
    """Critical: Ensure TARGET_CHANNEL_ID can be cast to an integer."""
    channel_id = env_vars.get("TARGET_CHANNEL_ID")
    assert channel_id.isdigit(), "TARGET_CHANNEL_ID must be a numeric string."

