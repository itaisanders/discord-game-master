# 🗺️ Project Roadmap: The Vibe & The Vision

This roadmap defines the "North Star" for the **Discord RPG Game Master Bot**. Instead of a rigid feature list, we focus on **Pillars of Experience**—ensuring every change enhances the "vibe" of an immersive, living TTRPG session.

---

## 🌟 The North Star
To create an AI Game Master that feels less like a chat bot and more like a creative collaborator who shares the table's excitement, respects the dice, and builds a world that breathes.

---

## 🏛️ Strategic Pillars

### 1. Narrative Integrity ("The Vibe")
*Focus: Pacing, atmosphere, and "Fiction-First" logic.*
- **Phase 1**: Refine Sensory Imagery (Moving from "You see a room" to "The smell of ozone and damp stone fills the air").
- **Phase 2**: Vocal Session Summaries (Audio-driven recaps of the last active session for returning players).
- **Phase 3**: NPC Voice Consistency (Each NPC having distinct verbal tics or attitudes stored in memory).

### 2. Deep Memory ("The World Breathes")
*Focus: Long-term consequences and living world state.*
- **Phase 1**: Regional Ledgers (Specific lore for different city districts).
- **Phase 2**: Relationship Webs (Tracking how NPCs feel about individual players, not just the party).
- **Phase 3**: Faction Clocks (Hidden clocks that advance world events based on player (in)action).

### 3. Mechanical Seamlessness ("Invisible Engine")
*Focus: Reducing "Bot speak" while maintaining rules accuracy.*
- **Phase 1**: True Randomness & Polish (Implementing Python-based dice rolls and solidifying output formatting/char-limit handling).
- **Phase 2**: Context-Full Knowledge (Transitioning from RAG to full-context rulebook ingestion for zero-hallucination rules mastery).
- **Phase 3**: Table State Machine (Architectural separation of meta-gaming/OOC discussion from narrative flow).

### 4. Architectural Flexibility ("Open GM")
*Focus: Modular design and local control.*
- **Phase 1**: Modular AI Provider (Configurable backend to allow swapping Gemini for local Ollama instances).
- **Phase 2**: Custom Move Injection (Allowing the AI to create unique situational "Moves" on the fly).
- **Phase 3**: AI-to-AI "Architect" Mode (One AI narrates, another manages world logic in the background).

### 5. Player Feedback Loop ("The GM Listens")
*Focus: Systematically gathering and learning from player feedback to improve GM performance.*
- **Phase 1**: Explicit feedback commands.
- **Phase 2**: Implicit feedback analysis.

---

## 📅 High-Level Milestones

### 🟢 Phase 1: Foundation (Current Focus)
- [x] Async-First Architecture (Stability)
- [x] RAG Rule Ingestion (Initial Accuracy)
- [x] Persistent .ledger Memory (State)
- [x] **True Randomness**: Move dice rolling from AI to Python code.
- [x] **Native Slash Commands**: Implement all user available commands as slash commands.
- [x] **Modularize the code**: Refactor the code into modules.
- [x] **Couple Personas to Modules**: Distribute the personas .md files from the personas folder into their appropriate modules folders
    - Change modules structure if needed.
- [x] **Output Polish**: Force bot output to be formatted to fit character limit, handle character limit and formatting faults gracefully instead of breaking the output into multiple messages.
- [x] **Modular Provider (Alpha)**: Initial support for configurable model backends (Ollama/Custom).

### 🟡 Phase 2: expansion
- [x] **Context-Full Knowledge**: Replace RAG with direct Markdown context ingestion for rulebooks.
- [x] **Away Mode**: Allow players to mark themselves as absent for a session with configurable character handling (ignore character, play as NPC, or narrative excuse).
- [x] **Stars and Wishes**: Implement a player feedback system.
    - `/stars [message]`: Players highlight something they enjoyed.
    - `/wishes [message]`: Players suggest something they'd like to see in the future.
    - Implicit Feedback: The AI will be instructed to analyze player messages for sentiment and content that can be interpreted as a "star" or a "wish". If the AI deems the feedback to be valid, it will be added to the feedback database via the feedback protocol.
- [x] **Table State Machine**: Implement session phase and OOC vs IC state management to prevent meta-bleed.
    - [x] **Session Zero**: Initial state for world-building and character creation.
    - [x] **States**: `IDLE`, `SESSION_ZERO`, `ACTIVE`, `PAUSED`, `DEBRIEF`.
    - [x] **Commands**: `/session [start|zero|pause|resume|end|close]` to manage flow.
- [x] **Cinematic Text Recaps**: Narrative-rich storytelling summarizing recent events.
    - **Goal**: Create a "TV-Show Recap" vibe ("Previously, on Spire...") in text form.
    - **Tech**: Dedicated 'Scriptwriter' persona.
    - **Commands**:
        - `/summary [scope]`: Trigger text generation.
        - `/voice` commands preserved for future Audio integration.
- [ ] **Dedicated Player Ledger**: Refactor the current players mapping in `party.ledger` into a dedicated `players.ledger` to centralize User ID, username, and character name associations, making it more robust and easier to manage.
    - `/party`: List all players in the campaign along with their characters and their current status (ephemeral).
- [ ] **Atmosphere 2.0**: Refined visual generation styles and ambient task suggestions.

### 🔴 Phase 3: Mastery
- [ ] **Cinematic Audio (The Bard 2.0)**: Enable TTS integration for the `/summary` command once API capabilities allow.
- [ ] Multi-Modal World-Building (AI generates maps based on session history)
- [ ] Faction System (The world moves around the players)
- [ ] Campaign Archiving (Exporting the campaign as a high-fidelity narrative "booklet")

---

## 🧪 Vibe-Coding Principles
1. **Fiction-First**: If a mechanic gets in the way of a great story, the story wins.
2. **Respect the Dice**: The AI never fudges; rolls are handled by code to ensure raw consequence.
3. **Show, Don't Just Tell**: Descriptions should favor atmosphere over clinical exposition.

> Refer to [AGENTS.md](./AGENTS.md) for agent guidelines.
