
import re
import time
from prettytable import PrettyTable
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from src.modules.dice.rolling import roll
from src.modules.presence.manager import AwayManager

# Global logic needs to be careful about state.
# pending_rolls was global in bot.py. 
# We should probably pass it in or manage it here if it's parser-specific state.
# Since process_roll_calls writes to it, let's keep it here.
pending_rolls = {}

# AwayManager is stateful but backed by file, so instantiating here is okay 
# provided we don't need to share in-memory cache with other modules excessively.
# ideally we'd pass it in, but for now specific instantiation is fine.
away_manager = AwayManager() 

def process_dice_rolls(text):
    """Intercepts DICE_ROLL protocol blocks and executes actual dice rolls."""
    # Pattern: ```DICE_ROLL\n[Character Name] rolls [dice notation] for [reason]\n```
    dice_pattern = r'```DICE_ROLL\s*(.+?)\s+rolls?\s+([^\s]+)(?:\s+for\s+(.+?))?\s*```'
    
    def replace_with_roll(match):
        character_name = match.group(1).strip()
        notation = match.group(2).strip()
        reason = match.group(3).strip() if match.group(3) else "unknown reason"
        
        result = roll(notation)
        
        if result.error:
            return f"❌ **{character_name}** attempted to roll {notation} but: {result.error}"
        
        return f"🎲 **{character_name}** rolls {notation} for {reason}: {result.formatted}"
    
    processed = re.sub(dice_pattern, replace_with_roll, text, flags=re.DOTALL | re.IGNORECASE)
    
    # Debug logging
    if "DICE_ROLL" in text.upper() and processed != text:
        print("🎲 Intercepted and executed DICE_ROLL block")
    
    return processed

def filter_away_mentions(text):
    """
    Removes mentions (<@ID>) for users who are currently Away.
    This acts as a safety net if the AI hallucinates a tag despite instructions.
    """
    away_users = away_manager.get_all_away_users()
    if not away_users:
        return text

    processed = text
    for user_id in away_users:
        # Check for standard mention format <@123456>
        mention_pattern = rf"<@!?{user_id}>"
        if re.search(mention_pattern, processed):
            print(f"🛡️ Suppressed mention for away user {user_id}")
            # Replace with a generic name reference or just strip it.
            # Stripping it might break grammar, but preventing the ping is priority.
            # We'll replace it with their display name if possible, or just "the character".
            processed = re.sub(mention_pattern, "**(Away)**", processed)
            
    return processed

def process_roll_calls(text):
    """
    Intercepts ROLL_CALL protocol blocks and stores pending rolls.
    
    Format:
    ```ROLL_CALL
    @Username: 2d6+3 for Defy Danger
    ```
    """
    global pending_rolls
    
    roll_call_pattern = r'```ROLL_CALL\s*(.*?)\s*```'
    
    def extract_and_store(match):
        content = match.group(1).strip()
        lines = content.split('\n')
        
        stored_calls = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Parse: @Username: 2d6+3 for Reason
            # We allow optional @
            call_pattern = r'@?(\w+):\s*([^\s]+)(?:\s+for\s+(.+))?'
            call_match = re.match(call_pattern, line, re.IGNORECASE)
            
            if call_match:
                username = call_match.group(1)
                notation = call_match.group(2)
                reason = call_match.group(3).strip() if call_match.group(3) else "unknown"
                
                # Store in pending_rolls keyed by username
                pending_rolls[username] = {
                    "notation": notation,
                    "reason": reason,
                    "timestamp": time.time()
                }
                
                stored_calls.append({
                    "username": username,
                    "notation": notation,
                    "reason": reason
                })
        
        # Return a user-friendly message
        if stored_calls:
            messages = [f"📋 **{call['username']}**, roll {call['notation']} for {call['reason']}" 
                       for call in stored_calls]
            return "\n".join(messages)
        return ""
    
    processed = re.sub(roll_call_pattern, extract_and_store, text, flags=re.DOTALL | re.IGNORECASE)
    
    if "ROLL_CALL" in text.upper() and processed != text:
        print("📋 Intercepted ROLL_CALL block")
    
    return processed

def render_table_as_ascii(match):
    """
    Processes a DATA_TABLE block into a PrettyTable ASCII string.
    """
    table_block = match.group(1)
    try:
        lines = [l.strip() for l in table_block.strip().split('\n') if l.strip()]
        title = "Data Table"
        headers = []
        rows = []
        
        for line in lines:
            if line.startswith("Title:"):
                title = line.replace("Title:", "").strip()
            elif "|" in line:
                cols = [c.strip() for c in line.split('|')]
                if not headers:
                    headers = cols
                else:
                    rows.append(cols)
        
        if headers:
            pt = PrettyTable()
            pt.field_names = headers
            pt.align = "l"
            pt.border = True
            
            for row in rows:
                if len(row) < len(headers):
                    row.extend(["" ] * (len(headers) - len(row)))
                pt.add_row(row[:len(headers)])
            
            return f"**{title}**\n```text\n{pt.get_string()}\n```"
    except Exception as e:
        print(f"⚠️ Failed to parse DATA_TABLE: {e}")
        return match.group(0)
    return match.group(0)

def process_response_formatting(text):
    """
    Handles all regex-based replacements and extractions (DATA_TABLE, MEMORY_UPDATE, VISUAL_PROMPT).
    """
    
    # 0. Safety Net: Filter Away Mentions
    text = filter_away_mentions(text)

    # 1. DATA_TABLE (Case Insensitive + Flexible Whitespace)
    data_table_pattern = r"```DATA_TABLE\s*(.*?)```"
    if re.search(data_table_pattern, text, re.DOTALL | re.IGNORECASE):
        print("🔍 Found DATA_TABLE block.")
    text = re.sub(data_table_pattern, render_table_as_ascii, text, flags=re.DOTALL | re.IGNORECASE).strip()
    
    memory_update_pattern = r"```MEMORY_UPDATE\s*(.*?)```"
    memory_match = re.search(memory_update_pattern, text, re.DOTALL | re.IGNORECASE)
    facts = None
    if memory_match:
        print("🔍 Found MEMORY_UPDATE block.")
        facts = memory_match.group(1).strip()
        text = re.sub(memory_update_pattern, "", text, flags=re.DOTALL | re.IGNORECASE).strip()
        
    # 3. VISUAL_PROMPT 
    # Primary: Backticked block
    visual_prompt_pattern = r"```VISUAL_PROMPT\s*(.*?)```"
    visual_match = re.search(visual_prompt_pattern, text, re.DOTALL | re.IGNORECASE)
    visual_prompt = None
    if visual_match:
        print("🔍 Found backticked VISUAL_PROMPT.")
        visual_prompt = visual_match.group(1).strip()
        text = re.sub(visual_prompt_pattern, "", text, flags=re.DOTALL | re.IGNORECASE).strip()
    else:
        # Fallback: Header + the Structure brackets (for when AI forgets backticks or uses bolding)
        # We look for the keyword and then any sequence of [...] blocks
        fallback_pattern = r"(?!\*+|#+)?\s*VISUAL_PROMPT\s*(?!\*+|#+)?(?:[:-])?\s*((?:\\\\[.*?\\\\]\s*)+)"
        fallback_match = re.search(fallback_pattern, text, re.DOTALL | re.IGNORECASE)
        if fallback_match:
            print("🔍 Found fallback VISUAL_PROMPT structure.")
            visual_prompt = fallback_match.group(1).strip()
            text = re.sub(fallback_pattern, "", text, flags=re.DOTALL | re.IGNORECASE).strip()

    if not visual_prompt and "VISUAL_PROMPT" in text.upper():
        print("⚠️ Found 'VISUAL_PROMPT' keyword but failed to parse the structure.")
    
    # 4. DICE_ROLL - Intercept and execute actual dice rolls
    text = process_dice_rolls(text)

    # 5. ROLL_CALL - Intercept and queue pending rolls
    text = process_roll_calls(text)

    return text, facts, visual_prompt

def check_length_violation(text, limit=1900):
    """
    Checks if the narrative portion of the text exceeds the character limit.
    Assumes 'text' is the processed narrative (protocols stripped).
    """
    return len(text) > limit

def smart_chunk_text(text, limit=1900):
    """
    Splits text into chunks respecting the limit, prioritizing:
    1. Paragraph breaks (\\n\\n)
    2. Line breaks (\\n)
    3. Sentence endings (. )
    4. Hard limit
    """
    if len(text) <= limit:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    # Strategy 1: Split by Paragraphs
    # We use a custom split to preserve empty lines if needed, but standard split is fine for now
    paragraphs = text.split('\n\n')
    
    for para in paragraphs:
        # Check if adding this paragraph exceeds limit
        # +2 for the \n\n we removed
        if len(current_chunk) + len(para) + 2 <= limit:
            current_chunk += para + "\n\n"
        else:
            # Current chunk is full, push it
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            
            # Now handle the new paragraph 'para'
            if len(para) <= limit:
                current_chunk = para + "\n\n"
            else:
                # Paragraph itself is too huge. Strategy 2: Split by Lines
                lines = para.split('\n')
                for line in lines:
                    if len(current_chunk) + len(line) + 1 <= limit:
                         current_chunk += line + "\n"
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                            current_chunk = ""
                        
                        if len(line) <= limit:
                            current_chunk = line + "\n"
                        else:
                             # Line is too huge. Strategy 3: Hard split
                            while len(line) > limit:
                                chunks.append(line[:limit])
                                line = line[limit:]
                            current_chunk = line + "\n"
                            
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks
