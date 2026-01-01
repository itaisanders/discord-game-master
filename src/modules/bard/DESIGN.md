# Bard Module Design (Cinematic Vocal Recaps)

## Overview
The **Bard Module** generates immersive, high-quality audio summaries. It uses a specialized "Scriptwriter" persona to transform session data into a dramatic script, which is then performed by a configurable AI TTS engine.

## Data Structures

### VoiceDefinition (TypedDict)
```python
{
    "name": str,         # User-friendly name (e.g., "The Ancient One")
    "provider_id": str,  # Actual ID used by the TTS engine
    "style": str         # Description of the voice's tone/vibe
}
```

### BardSettings (JSON Schema)
```json
{
  "selected_voice_key": "string",
  "last_summary_timestamp": "ISO8601 String"
}
```

## Public Interface

### `BardManager` (src/modules/bard/manager.py)

#### `get_voice_registry() -> dict[str, VoiceDefinition]`
Returns the full dictionary of available voices configured by the instance owner.

#### `get_selected_voice() -> VoiceDefinition`
Returns the currently active voice definition based on persistence.

#### `set_selected_voice(voice_key: str) -> bool`
Updates the preferred voice. Returns `False` if the key is invalid.

### `Scriptwriter` (src/modules/bard/scriptwriter.py)

#### `generate_script(history: list[discord.Message], context: str) -> str`
- **Input**: Recent message history and relevant `world.ledger` context.
- **Persona**: Uses `src/modules/bard/narrator_persona.md`.
- **Output**: A dramatic prose script optimized for audio (no markdown, includes stage directions like `[PAUSE]`).

### `AudioPerformer` (src/core/tts_interface.py)

#### `perform(script: str, voice_id: str) -> io.BytesIO`
- **Input**: The text script and the provider-specific voice ID.
- **Output**: A byte stream of the generated audio (MP3/WAV).

## Narrative Persona: The Scriptwriter
**Location**: `src/modules/bard/narrator_persona.md`

### Responsibilities:
1.  **Synthesize**: Condense complex tactical combat or long dialogue into dramatic beats.
2.  **Flavor**: Use the game's setting (e.g., "The Spire") to theme the language.
3.  **Structure**: Always follow a "Beginning -> Conflict -> Cliffhanger" arc.
4.  **TTS-Optimization**: Avoid complex punctuation that trips up AI; use simple sentences for maximum impact.

## Slash Commands

| Command | Arguments | Logic |
| :--- | :--- | :--- |
| `/summary` | `scope: [Session\|Campaign]` | Calls `generate_script` -> `perform` -> Sends File. |
| `/voice list` | None | Renders the Voice Registry as an ASCII table. |
| `/voice set` | `name: String` | Calls `manager.set_selected_voice`. |

### Initialization Logic
The slash commands for the Bard module (specifically `/voice` and `/summary`) **must not be registered** if the Voice Registry is empty or unconfigured. 
- **Check**: `BardManager` must implement a `is_configured()` method.
- **Action**: In `main.py`, verify `bard_manager.is_configured()` before calling `register_bard_commands()`.