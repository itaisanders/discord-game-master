"""
Dice Rolling System for Discord RPG Game Master Bot

Provides cryptographically secure dice rolling using Python's secrets module.
Ensures "Respect the Dice" principle - all randomness is genuine, never simulated.

Author: Game Master Bot Team
License: MIT
"""

import re
import secrets
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DiceResult:
    """
    Represents the result of a dice roll.
    
    Attributes:
        notation: Original dice notation string (e.g., "2d6+3")
        rolls: List of individual die results (e.g., [4, 5])
        modifier: Numeric modifier applied (e.g., 3)
        total: Final sum of rolls + modifier (e.g., 12)
        formatted: Discord-ready formatted string (e.g., "🎲 [4, 5] +3 = **12**")
        error: Optional error message if notation is invalid
    """
    notation: str
    rolls: List[int]
    modifier: int
    total: int
    formatted: str
    error: Optional[str] = None


def roll(notation: str) -> DiceResult:
    """
    Roll dice using cryptographically secure randomness.
    
    Supports standard TTRPG dice notation:
    - Basic: 1d20, 2d6, 3d8
    - Modifiers: 2d6+3, 1d20-2, 4d8+5
    - Percentile: 1d100, d%
    - FATE dice: 4dF
    
    Args:
        notation: Dice notation string (e.g., "2d6+3")
    
    Returns:
        DiceResult object with roll results and formatted output
    
    Examples:
        >>> result = roll("2d6+3")
        >>> print(result.formatted)
        🎲 [4, 5] +3 = **12**
        
        >>> result = roll("1d20")
        >>> print(result.total)
        15
    """
    notation = notation.strip()
    original_notation = notation
    
    # Dice notation regex: (count)d(size)(pool?)(modifier)
    # Examples: 2d6+3, 1d20, d%, 4dF, 5d6p
    pattern = r'^(\d+)?d(\d+|%|F)(p|pool)?([+-]\d+)?$'
    match = re.match(pattern, notation, re.IGNORECASE)
    
    if not match:
        return DiceResult(
            notation=original_notation,
            rolls=[],
            modifier=0,
            total=0,
            formatted="",
            error=f"Invalid dice notation. Use format like '2d6+3', '1d20', 'd%', or '4dF'"
        )
    
    # Parse components
    count_str = match.group(1)
    size_str = match.group(2)
    is_pool = bool(match.group(3))
    modifier_str = match.group(4)
    
    # Default count is 1 if not specified (e.g., "d20" = "1d20")
    count = int(count_str) if count_str else 1
    
    # Parse modifier
    modifier = int(modifier_str) if modifier_str else 0
    
    # Validation: Pool cannot have modifiers
    if is_pool and modifier != 0:
        return DiceResult(
            notation=original_notation,
            rolls=[],
            modifier=0,
            total=0,
            formatted="",
            error="Dice pools do not support modifiers (modifiers affect dice count). Use e.g. '5d6p'."
        )
    
    # Validation: dice count
    if count <= 0:
        return DiceResult(
            notation=original_notation,
            rolls=[],
            modifier=0,
            total=0,
            formatted="",
            error="Dice count must be positive"
        )
    
    if count > 100:
        return DiceResult(
            notation=original_notation,
            rolls=[],
            modifier=0,
            total=0,
            formatted="",
            error="Maximum 100 dice per roll (to prevent spam)"
        )
    
    # Handle special dice types
    if size_str.upper() == 'F':
        # FATE dice: -1, 0, or +1
        rolls = [secrets.randbelow(3) - 1 for _ in range(count)]
        total = sum(rolls) + modifier
        
        # Format FATE dice specially
        fate_symbols = {-1: "[-]", 0: "[ ]", 1: "[+]"}
        rolls_str = " ".join(fate_symbols[r] for r in rolls)
        
        if modifier != 0:
            mod_str = f" {modifier:+d}"
            formatted = f"{rolls_str}{mod_str} = **{total}**"
        else:
            formatted = f"{rolls_str} = **{total}**"
        
        return DiceResult(
            notation=original_notation,
            rolls=rolls,
            modifier=modifier,
            total=total,
            formatted=formatted,
            error=None
        )
    
    elif size_str == '%':
        # Percentile dice (1-100)
        size = 100
    else:
        # Standard numeric dice
        size = int(size_str)
    
    # Validation: dice size
    if size <= 0:
        return DiceResult(
            notation=original_notation,
            rolls=[],
            modifier=0,
            total=0,
            formatted="",
            error="Dice size must be positive"
        )
    
    if size > 1000:
        return DiceResult(
            notation=original_notation,
            rolls=[],
            modifier=0,
            total=0,
            formatted="",
            error="Maximum d1000 dice size (to prevent abuse)"
        )
    
    # Roll the dice using cryptographically secure randomness
    # secrets.randbelow(n) returns 0 to n-1, so we add 1 to get 1 to n
    rolls = [secrets.randbelow(size) + 1 for _ in range(count)]
    
    # Calculate total
    total = sum(rolls) + modifier
    
    # Format output for Discord
    if is_pool:
        # Dice pool: just show the list of rolls, no total
        formatted = f"{rolls}"
    elif count == 1:
        # Single die: just show the result
        if modifier != 0:
            formatted = f"**{rolls[0]}** {modifier:+d} = **{total}**"
        else:
            formatted = f"**{rolls[0]}**"
    else:
        # Multiple dice: show individual rolls
        rolls_str = str(rolls)
        if modifier != 0:
            formatted = f"{rolls_str} {modifier:+d} = **{total}**"
        else:
            formatted = f"{rolls_str} = **{total}**"
    
    return DiceResult(
        notation=original_notation,
        rolls=rolls,
        modifier=modifier,
        total=total,
        formatted=formatted,
        error=None
    )


# CLI testing interface
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Command line usage: python dice.py 2d6+3
        notation = " ".join(sys.argv[1:])
        result = roll(notation)
        
        if result.error:
            print(f"❌ Error: {result.error}")
        else:
            print(f"🎲 Rolling {result.notation}: {result.formatted}")
    else:
        # Interactive mode
        print("🎲 Dice Roller - Interactive Mode")
        print("Enter dice notation (e.g., 2d6+3, 1d20, d%, 4dF)")
        print("Type 'exit' to quit\n")
        
        while True:
            try:
                notation = input("Roll: ").strip()
                if notation.lower() in ['exit', 'quit', 'q']:
                    break
                
                if not notation:
                    continue
                
                result = roll(notation)
                
                if result.error:
                    print(f"❌ Error: {result.error}\n")
                else:
                    print(f"🎲 {result.formatted}\n")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}\n")
