# 🎲 Discord RPG Game Master Bot

The **Discord RPG Game Master Bot** is an advanced AI-powered Game Master for multiplayer, text-based tabletop RPGs. Powered by Google's Gemini API (Gemini 2.0 Flash Lite), it facilitates immersive, "Fiction-First" gameplay through **native Discord Slash Commands**.

It features **Async-First Execution** for a non-blocking Discord experience, **RAG (Retrieval-Augmented Generation)** to index game rules from PDF sourcebooks, **Conversational Memory** to track party context, and a persistent **Master Ledger** system.

---

## 🚀 Key Features

*   **Async-First Design**: Optimized for Discord; all AI computations run asynchronously to prevent connection drops.
*   **Professional GM Persona**: Follows a strict "Play to Find Out" philosophy, managing spotlight, pacing, and mechanics through **intuitive slash commands**.
*   **Comprehensive Slash Commands**: 
    *   `/help` for a full list of commands.
    *   `/sheet` to view character details.
    *   `/ledger` for campaign history and facts.
    *   `/visual` to request atmospheric images.
    *   `/ooc` for out-of-character communication.
    *   `/rewind` to undo narrative turns.
    *   `/x` for safety pivots.
    *   `/reset_memory` (admin only) to rebuild campaign memory.
*   **Context-Full Knowledge**: Ingests high-fidelity Markdown rulebooks directly into the AI's system context for zero-hallucination accuracy.
*   **True Randomness**: All dice rolls use Python's cryptographically secure `secrets` module - AI never simulates results.
*   **Persistent Memory**: Manages multiple players via the **Master Ledger** system across sessions.
*   **Multimedia Integration**: Generates atmospheric visuals via specialized image generation protocols.

---

## 🛠️ Setup & Installation

### 1. Prerequisites
*   Python 3.10+
*   A Discord Bot Token (from [Discord Developer Portal](https://discord.com/developers/applications))
*   A Google Gemini API Key (from [Google AI Studio](https://aistudio.google.com/))

### 2. Installation
Clone the repository and install dependencies:
```bash
git clone <your-repo-ur>
cd game-master
pip install -r requirements.txt
# (or if you don't have a requirements file yet, see dependencies below)
pip install discord.py google-genai python-dotenv
```

### 3. Configuration
1.  Copy the example environment file:
    ```bash
    cp .env.example .env
    ```
2.  Edit `.env` and fill in your credentials:
    *   `DISCORD_TOKEN`: Your valid Discord bot token.
    *   `GEMINI_API_KEY`: Your Gemini API key.
    *   `TARGET_CHANNEL_ID`: Copy the ID of the specific Discord channel the bot should listen to (Enable Developer Mode in Discord -> Right Click Channel -> Copy ID).
    *   `AI_MODEL`: `gemini-2.0-flash-lite` (default).

---

## 📚 Knowledge Base Ingestion

To provide the bot with rulebook knowledge, you must transcribe your RPG sourcebooks into Markdown.

1.  Place your `.pdf` rulebooks into the `pdf/` directory.
2.  Use the **High-Fidelity RPG Ingestion** tool below to create Markdown versions in the `knowledge/` directory.
3.  The bot automatically loads all `.md` files from `knowledge/` on startup.

---

For superior narrative accuracy, use the **RPG Scribe** tool to convert complex PDFs into high-fidelity Markdown. This is highly recommended for rules-heavy systems like *Spire* or *Blades in the Dark*.

### 1. Requirements
Ensure you have the AI layout extensions installed:
```bash
pip install -U "pymupdf4llm[ocr,layout]"
```

### 2. Run Ingestion
```bash
python scripts/ingest_rpg_book.py pdf/your_book.pdf
```
*   **Logic**: It performs high-fidelity layout analysis using `pymupdf4llm` to preserve tables, lists, and mechanical stats.
*   **Output**: Saves a `.md` file to the `knowledge/` directory which the bot loads automatically on startup.

---

## ▶️ Running the Bot

For persistent remote operation, use the provided management script.

### Bot Management (`manage.sh`)
This script allows you to run the bot as a persistent background process.

*   **Start the bot:**
    ```bash
    ./manage.sh start
    ```
*   **Stop the bot:**
    ```bash
    ./manage.sh stop
    ```
*   **Restart the bot:**
    ```bash
    ./manage.sh restart
    ```
*   **Check the status:**
    ```bash
    ./manage.sh status
    ```
*   **View recent logs:**
    ```bash
    ./manage.sh log
    ```

## 🎮 How to Run

### Manual Foreground Mode
For local testing, you can run the bot directly. Note that closing the terminal will stop the bot.

#### Discord Mode (Live)
Run the bot to start listening to your Discord channel:
```bash
python3 bot.py
```
*   **Interaction**: The bot only responds in the channel specified by `TARGET_CHANNEL_ID`.
*   **Commands**: All player interactions are now handled exclusively via native Discord Slash Commands (e.g., `/roll`, `/sheet`, `/help`).

#### Terminal Mode (Testing)
Test the GM persona and logic directly in your console without sending messages to Discord:
```bash
python3 bot.py --terminal
```
*   You act as `User [@Terminal]`.
*   Great for testing prompts, rules knowledge, and persona consistency.
*   Type `exit` or `quit` to stop.

---

## 🎲 Dice Rolling System

The bot implements **"Respect the Dice"** - all randomness comes from Python's `secrets` module, never from AI simulation.

### Manual Rolls
Players can roll dice manually using the `/roll` slash command:
```
/roll 2d6+3
/roll 1d20
/roll 4dF
```

### Supported Notation
- **Basic**: `1d20`, `2d6`, `3d8` (roll N dice of size D)
- **Modifiers**: `2d6+3`, `1d20-2` (add/subtract modifier)
- **Percentile**: `1d100` or `d%` (roll 1-100)
- **FATE Dice**: `4dF` (roll 4 FATE dice, each -1/0/+1)
- **Dice Pool**: `5d6p` (roll N dice, list results, no sum)

### AI-Requested Rolls
When the GM needs a roll, it will request one via the `DICE_ROLL` protocol. The bot intercepts these requests and executes actual random rolls.

**Example**:
```
GM: "Alistair, you'll need to Defy Danger. Roll 2d6+3."
[Bot executes: 🎲 Alistair rolls 2d6+3 for Defy Danger: [4, 5] +3 = **12**]
GM: "A 12! You leap across the chasm with grace..."
```

### Player Roll Requests
The GM can also queue dice rolls for you. If the GM says "Roll 2d6+3", you can just type `/roll` (without arguments) to execute the pending roll:

**Example**:
```
GM: 📋 **Alistair**, roll 2d6+3 for Defy Danger
Player: /roll
Bot: 🎲 **Alistair** rolls 2d6+3 for Defy Danger: [4, 5] +3 = **12**
```

---

## 💤 Away Mode System

When real life calls, players can mark themselves as Away without pausing the game for everyone else.

### Commands
*   `/away [mode]`: Set your status.
    *   **Auto-Pilot**: The GM takes over your character (roleplays + rolls).
    *   **Off-Screen**: Your character is present but passive/silent.
    *   **Narrative Exit**: Your character leaves the scene entirely.
*   `/back`: Return to the game.
    *   Generates a personalized **Catch-Up Summary** of what you missed.
    *   Announces your return to the party.

### Features
*   **Mention Supression**: The GM will not mention/ping you while you are away.
*   **Context Awareness**: The AI knows who is away and adjusts the narrative spotlight accordingly.

---

## 🧩 Project Structure

*   `bot.py`: Main application logic (Discord client + Terminal loop).
*   `manage.sh`: Management script for starting/stopping the bot as a background process.
*   `scripts/index_knowledge.py`: Utility to scan `pdf/` and update the RAG store.
*   `scripts/ingest_rpg_book.py`: Local high-fidelity RPG book transcription tool.
*   `scripts/check_env.py`: Environment validation utility.
*   `personas/gm_persona.md`: The "System Instructions" defining the GM's behavior and rules.
*   `pdf/`: Directory for your game rulebooks.
*   `tests/`: Automated test suite (run via `pytest`).

---

## 🏛️ Strategic Documentation

For deeper insight into the bot's operation and development:

- **[AGENTS.md](./AGENTS.md)**: The **Architectural Source of Truth**. Contains logic patterns, domain constraints, and development protocols for AI agents.
- **[roadmap.md](./roadmap.md)**: The **Project Vision**. Outlines the "North Star" and strategic "vibe-coding" pillars.

---

## 🧪 Testing
Run the automated test suite to verify environment integrity and API access:
```bash
pytest
```

---

## 🎨 Credits & Game Design Attributions

This project implements narrative and mechanical logic derived from various tabletop RPG design philosophies. Please see [ATTRIBUTION.md](./ATTRIBUTION.md) for full details and licensing information regarding these game systems.

## ⚖️ License & Attribution

This project is licensed under the **MIT License**.

### Third-Party Libraries
*   [discord.py](https://github.com/Rapptz/discord.py) — MIT License
*   [google-genai](https://github.com/google/generative-ai-python) — Apache License 2.0
*   [python-dotenv](https://github.com/theskumar/python-dotenv) — BSD-3-Clause License
*   [pytest](https://github.com/pytest-dev/pytest) — MIT License
