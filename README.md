# 🎲 Apex Game Master Bot

The **Apex Game Master** is an advanced Discord bot powered by Google's Gemini API (Gemini 2.0 Flash Lite). It is designed to act as an immersive, "Fiction-First" Game Master for multiplayer tabletop RPGs like *Spire*, *Blades in the Dark*, or *D&D*.

It features **RAG (Retrieval-Augmented Generation)** to index game rules from PDF sourcebooks, **Conversational Memory** to track party context, and a persistent **Master Ledger** to manage multiple players.

---

## 🚀 Features

*   **Professional GM Persona**: Follows a strict "Play to Find Out" philosophy, managing spotlight, pacing, and mechanics.
*   **Knowledge Base**: Automatically indexes PDF rulebooks (e.g., *Spire*) to answer rule queries accurately.
*   **Multiplayer Context**: Intelligently tracks different Discord users as distinct characters (e.g., `User [@Player1]`).
*   **Dual Mode**: Run as a Discord Bot or test offline in **Terminal Mode**.
*   **Safety Override**: Safety filters are set to `BLOCK_NONE` to allow for mature storytelling and combat descriptions required in TTRPGs.

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

## 📚 Knowledge Base Indexing (RAG)

Before running the bot, you must index your game sourcebooks.

1.  Place your `.pdf` rulebooks into the `pdf/` directory.
2.  Run the indexer script:
    ```bash
    python scripts/index_knowledge.py
    ```
3.  This script will upload the PDFs to Google's GenAI File Store and automatically update your `.env` file with a new `STORE_ID`.

---

## 📜 High-Fidelity RPG Ingestion (Optional)

For superior narrative accuracy, use the **RPG Scribe** tool to convert complex PDFs into verbatim Markdown. This is highly recommended for rules-heavy systems like *Spire* or *Blades in the Dark*.

### 1. Requirements
Ensure you have the AI layout extensions installed:
```bash
pip install -U "pymupdf4llm[ocr,layout]"
```

### 2. Run Ingestion
```bash
python scripts/ingest_rpg_book.py pdf/your_book.pdf [--keep-temp]
```
*   **Visual Feedback**: The script uses a progress spinner and bar to show real-time status.
*   **Logic**: It performs AI-driven layout analysis and transcribes the book in 5-page chunks to ensure zero-omission of spells, gear, or mechanical stats.
*   **Optional Parameters**: Use `--keep-temp` to preserve the intermediate `_dump.md` and `_raw.txt` files in the `knowledge/` directory for manual review.
*   **Output**: Saves a high-fidelity `.md` file to the `knowledge/` directory.

---

## 🎮 How to Run

### Discord Mode (Live)
Run the bot to start listening to your Discord channel:
```bash
python bot.py
```
*   **Interaction**: The bot only responds in the channel specified by `TARGET_CHANNEL_ID`.
*   **Slash Commands**: Supports commands like `/roll`, `/sheet`, and `/visual` (parsed via natural language in this version).

### Terminal Mode (Testing)
Test the GM persona and logic directly in your console without sending messages to Discord:
```bash
python bot.py --terminal
```
*   You act as `User [@Terminal]`.
*   Great for testing prompts, RAG retrieval, and persona consistency.
*   Type `exit` or `quit` to stop.

---

## 🧩 Project Structure

*   `bot.py`: Main application logic (Discord client + Terminal loop).
*   `scripts/index_knowledge.py`: Utility to scan `pdf/` and update the RAG store.
*   `scripts/ingest_rpg_book.py`: High-fidelity RPG book transcription tool.
*   `scripts/check_env.py`: Environment validation utility.
*   `personas/gm_persona.md`: The "System Instructions" defining the GM's behavior and rules.
*   `pdf/`: Directory for your game rulebooks.
*   `tests/`: Automated test suite (run via `pytest`).

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
