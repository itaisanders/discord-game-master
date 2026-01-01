# Tasks

## In Progress

## Completed
- [x] **Table State Machine**: Implement session phase and OOC vs IC state management to prevent meta-bleed.
    - [x] **Step 1: Core Logic**
        - [x] Implement `src/modules/table/state.py`: Define `TableState` Enum and `TableManager` class with JSON persistence (`memory/table_state.json`).
    - [x] **Step 2: Verification (Unit Tests)**
        - [x] Create `tests/test_table_state.py`: Test state transitions, persistence, and `is_active()` logic.
        - [x] Run `pytest tests/test_table_state.py` to ensure core stability.
    - [x] **Step 3: Interface**
        - [x] Implement `src/modules/table/commands.py`: Create the `/session` slash command group with options (`start`, `zero`, `pause`, `resume`, `end`, `close`).
    - [x] **Step 4: Integration**
        - [x] Update `src/main.py`: Initialize `TableManager`, register commands, and gate the `on_message` narrative loop.
    - [x] **Step 5: Final Verification & Docs**
        - [x] Restart Bot / Run Terminal Mode to verify end-to-end flow.
        - [x] Align `ARCHITECTURE.md` and module `DESIGN.md` with final implementation.
        - [x] Commit changes.
- [x] **Stars and Wishes**: Implement a player feedback system.
    - [x] `/stars [message]`: Players highlight something they enjoyed. (Implemented in main.py)
    - [x] `/wishes [message]`: Players suggest something they'd like to see in the future. (Implemented in main.py)
    - [x] Implicit Feedback: The AI will be instructed to analyze player messages for sentiment and content that can be interpreted as a "star" or a "wish". If the AI deems the feedback to be valid, it will be added to the feedback database via the feedback protocol.
        - [x] Update `gm_persona.md` with instructions for `FEEDBACK_DETECTED` protocol.
        - [x] Update `parser.py` to extract `FEEDBACK_DETECTED` blocks.
        - [x] Update `main.py` to handle detected feedback and trigger `FeedbackConfirmView`.
    - [x] Create `src/modules/feedback/DESIGN.md`.
    - [x] Update `SPECS.md`.
- [x] **Modular Provider (Alpha)**: Initial support for configurable model backends (Ollama/Custom).
- [x] **Output Polish**: Implemented smart truncation, retry logic for long messages, and strict narrative limits in persona.
- [x] **Couple Personas to Modules**: Distributed persona markdown files into modules, refactored code for relative path loading, and removed global configuration.
