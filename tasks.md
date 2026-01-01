# Tasks

## In Progress
- [ ] **Dedicated Player Ledger**: Refactor `party.ledger` into a dedicated `players.ledger`.
    - [ ] Create `src/modules/memory/players_service.py` (or update existing service).
    - [ ] Implement `/party` slash command.
    - [ ] Migrate existing player data from `party.ledger` to `players.ledger`.
    - [ ] Update `gm_persona.md` and `architect_persona.md` to reflect the new ledger structure.

## Completed
- [x] **Cinematic Text Recaps (The Bard)**: Implement narrative-rich text summaries.
    - [x] **Design**: Created `src/modules/bard/DESIGN.md`.
    - [x] **Infrastructure**: Implemented `BardManager` and `Voice Registry`.
    - [x] **Persona**: Created `src/modules/bard/narrator_persona.md`.
    - [x] **Logic**: Implemented `scriptwriter.py` (LLM Script Generation).
    - [x] **Commands**: Implemented `/summary` (Text Mode) and `/voice` configuration.
    - [x] **Audio Infrastructure**: `TTSProvider` implemented but disabled (Future Phase).
- [x] **Table State Machine (Implicit)**: Implement implicit triggers for table state changes.
- [x] **Table State Machine**: Implement session phase and OOC vs IC state management to prevent meta-bleed.
- [x] **Table State Machine**: Implement session phase and OOC vs IC state management to prevent meta-bleed.
    - [x] **Implicit Protocol**: `TABLE_STATE` detection and `StateChangeView` UI.
    - [x] **Explicit Commands**: `/session` command for manual control.
    - [x] **Core Logic**: `TableManager` and JSON persistence.
- [x] **Stars and Wishes**: Implement a player feedback system.
- [x] **Modular Provider (Alpha)**: Initial support for configurable model backends.
- [x] **Output Polish**: Implemented smart truncation and retry logic.
- [x] **Couple Personas to Modules**: Distributed persona markdown files.

