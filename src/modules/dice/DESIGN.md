# Dice Module Design

## Overview
The `dice` module handles all Random Number Generation (RNG) and dice notation parsing. It strictly enforces "True Randomness" using cryptographic libraries.

## Public Interface

### `rolling.py`
The primary entry point for dice operations.

#### Functions
- **`roll(notation: str) -> DiceResult`**
    - **Description**: Parses a dice notation string and executes a cryptographically secure roll.
    - **Inputs**: 
        - `notation` (`str`): Standard TTRPG dice notation (e.g., `"2d6+3"`, `"1d20"`, `"3d6p"`, `"d%"`, `"4dF"`).
    - **Returns**: A `DiceResult` object containing the roll details.

## Data Structures

### `DiceResult` (Dataclass)
Represents the outcome of a dice roll.

```python
@dataclass
class DiceResult:
    notation: str          # Original input string (e.g., "2d6+3")
    rolls: List[int]       # List of individual die results (e.g., [4, 5])
    modifier: int          # The integer modifier added (e.g., 3)
    total: int             # Sum of rolls + modifier
    formatted: str         # Discord-markdown formatted result (e.g., "🎲 [4, 5] +3 = **12**")
    error: Optional[str]   # Error message if parsing failed, else None
```

### Constraints
- **Max Dice Count**: 100 (to prevent spam).
- **Max Dice Size**: d1000.
- **RNG Source**: Must use `secrets` module (SystemRandom), never `random` module.
