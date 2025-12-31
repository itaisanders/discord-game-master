
import os
import pathlib
import sys
import re
import time
from typing import Optional, List
from google.genai import types

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from src.core.config import AI_MODEL
from src.core.client import client_genai

# Load Persona (Dynamic Load)


def load_memory():
    """Loads all .ledger files from ./memory."""
    memory_parts = []
    memory_dir = pathlib.Path("./memory")
    if memory_dir.exists():
        for l_file in memory_dir.glob("*.ledger"):
            try:
                content = l_file.read_text(encoding="utf-8")
                memory_parts.append(f"\n--- CAMPAIGN LEDGER: {l_file.name} ---\n{content}")
            except Exception as e:
                print(f"❌ Failed to load ledger {l_file.name}: {e}")
    return "\n".join(memory_parts)

def save_ledger_files(response_text):
    """Parses FILE: blocks from AI response and saves them to ./memory."""
    count = 0
    try:
        # Parse ```FILE: filename.ledger\ncontent\n```
        file_pattern = r"```FILE: (.*?)\n(.*?)```"
        updates = re.findall(file_pattern, response_text, re.DOTALL)
        
        if not updates:
            # Try fallback for non-backticked blocks if any
            file_pattern_nb = r"FILE: (.*?\.ledger)\n(.*?)(?=FILE:|$)"
            updates = re.findall(file_pattern_nb, response_text, re.DOTALL)

        for filename, content in updates:
            filename = filename.strip()
            if not filename.endswith(".ledger"):
                filename += ".ledger"
            
            filepath = pathlib.Path("./memory") / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(content.strip(), encoding="utf-8")
            print(f"💾 Ledger Saved: {filename}")
            count += 1
    except Exception as e:
        print(f"❌ Error saving ledgers: {e}")
    return count

async def update_ledgers_logic(update_facts):
    """Uses the Memory Architect to update physical ledger files asynchronously."""
    try:
        current_memory = load_memory()
        # Relative path to architect persona
        current_dir = pathlib.Path(__file__).parent
        architect_persona_path = current_dir / "architect_persona.md"
        
        if not architect_persona_path.exists():
            print("⚠️ Memory Architect persona missing!")
            return
            
        persona_content = architect_persona_path.read_text(encoding="utf-8")
        
        prompt = f"# CURRENT LEDGER STATE\n{current_memory if current_memory else '[Empty]'}\n\n# NEW FACTS TO INCORPORATE\n{update_facts}"
        
        # Use AIO client to prevent blocking
        response = await client_genai.aio.models.generate_content(
            model=AI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=persona_content,
                temperature=0.1
            )
        )
        if response.text:
            save_ledger_files(response.text)
    except Exception as e:
        print(f"❌ Ledger Update Error: {e}")

async def reverse_ledgers_logic(facts_to_reverse):
    """Uses the Memory Architect to reverse facts in physical ledger files."""
    try:
        current_memory = load_memory()
        # Relative path to architect persona
        current_dir = pathlib.Path(__file__).parent
        architect_persona_path = current_dir / "architect_persona.md"

        if not architect_persona_path.exists():
            print("⚠️ Memory Architect persona missing!")
            return
            
        persona_content = architect_persona_path.read_text(encoding="utf-8")
        
        prompt = (
            f"# CURRENT LEDGER STATE\n{current_memory if current_memory else '[Empty]'}\n\n"
            f"# REWIND EVENT: The following facts are now INCORRECT and must be REVERSED or REMOVED from the ledgers:\n{facts_to_reverse}"
        )
        
        response = await client_genai.aio.models.generate_content(
            model=AI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=persona_content,
                temperature=0.1
            )
        )
        if response.text:
            save_ledger_files(response.text)
            print("⏪ Ledgers Reversed.")
    except Exception as e:
        print(f"❌ Ledger Reversal Error: {e}")

def get_character_name(user_id: str, user_name: str) -> Optional[str]:
    """
    Finds a character's name by searching the party.ledger for a matching
    Discord User ID or username.
    """
    party_ledger_path = pathlib.Path("./memory/party.ledger")
    if not party_ledger_path.exists():
        return None

    try:
        content = party_ledger_path.read_text(encoding="utf-8")
        lines = content.split('\n')
        
        # Simple table parsing, assuming Name is the first column and User is the second
        # and they are separated by '|'
        for line in lines:
            if not line.strip().startswith('|'):
                continue
                
            cols = [c.strip() for c in line.split('|')]
            if len(cols) > 2:
                name_col = cols[1].replace('**', '').strip()
                user_col = cols[2]
                
                # Check for ID match <@12345> or username match @username
                if f"<@{user_id}>" in user_col or f"@{user_name}" in user_col:
                    return name_col
    except Exception as e:
        print(f"Error parsing party.ledger for character name: {e}")
        return None
    
    return None

async def fetch_character_sheet(character_name: str) -> Optional[str]:
    """
    Retrieves a character's sheet from party.ledger by parsing for the character_sheet block.
    """
    party_ledger_path = pathlib.Path("./memory/party.ledger")
    if not party_ledger_path.exists():
        return None

    all_ledger_content = party_ledger_path.read_text(encoding="utf-8")

    # Regex to find the specific character_sheet block
    # It looks for ```character_sheet[char_name=CHARACTER_NAME]...```
    # re.escape is used for character_name to handle special characters correctly
    pattern = r"```character_sheet\[char_name=" + re.escape(character_name) + r"\].*?\n(.*?)```"
    match = re.search(pattern, all_ledger_content, re.DOTALL)

    if match:
        # Return the content inside the block
        return match.group(1).strip()
    else:
        return None

async def get_feedback_interpretation(feedback_type: str, message: str) -> str:
    """Uses the GM persona to interpret player feedback."""
    try:
        from src.core.config import AI_MODEL
        from src.core.client import client_genai
        from src.modules.narrative.loader import load_system_instruction
        
        persona_content = load_system_instruction()
        
        prompt = (
            f"A player has provided feedback. As the GM, your task is to understand their input and explain what you will do with it.\n\n"
            f"The feedback is a '{feedback_type.upper()}'. This means they {'liked something and want more of it' if feedback_type == 'star' else 'want to see something in the future'}.\n\n"
            f"**Player's Feedback:** \"{message}\"\n\n"
            f"**Your Interpretation:** Briefly explain your understanding of this feedback and how it might influence future sessions. Start with 'I understand...'. Then, create a ```FEEDBACK_UPDATE``` block containing a concise, structured fact for your long-term memory."
        )

        response = await client_genai.aio.models.generate_content(
            model=AI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=persona_content,
                temperature=0.7
            )
        )
        return response.text.strip()
    except Exception as e:
        print(f"❌ Feedback Interpretation Error: {e}")
        return "Sorry, I had trouble understanding that. Please try again."

async def record_feedback(feedback_type: str, user: str, message: str, interpretation: str):
    """Parses FEEDBACK_UPDATE and appends to feedback.ledger."""
    feedback_ledger_path = pathlib.Path("./memory/feedback.ledger")
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    feedback_pattern = r"```FEEDBACK_UPDATE\s*(.*?)```"
    match = re.search(feedback_pattern, interpretation, re.DOTALL | re.IGNORECASE)
    
    if not match:
        feedback_content = f"- [Raw Interpretation] {interpretation.split('```')[0].strip()}"
    else:
        feedback_content = match.group(1).strip()

    entry = f"# Entry added on {timestamp} from user {user}\n{feedback_content}\n\n"
    
    try:
        with open(feedback_ledger_path, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        print(f"❌ Failed to write to feedback.ledger: {e}")

async def rebuild_memory_from_history(history_text: str) -> int:
    """
    Rebuilds the ledgers based on the provided history text using the Memory Architect.
    """
    try:
        current_dir = pathlib.Path(__file__).parent
        architect_persona_path = current_dir / "architect_persona.md"
        
        if not architect_persona_path.exists():
            print("⚠️ Memory Architect persona missing!")
            return 0
            
        persona_content = architect_persona_path.read_text(encoding="utf-8")
        
        response = await client_genai.aio.models.generate_content(
            model=AI_MODEL,
            contents=f"# HISTORY\n{history_text}\n\nBuild fresh ledgers.",
            config=types.GenerateContentConfig(system_instruction=persona_content, temperature=0.1)
        )
        if response.text:
            return save_ledger_files(response.text)
    except Exception as e:
        print(f"❌ Memory Rebuild Error: {e}")
    return 0
