# Tasks

## In Progress
- [ ] **Dedicated Player Ledger**: Refactor `party.ledger` into a dedicated `players.ledger`.

## Completed
- [x] **Table State Machine (Implicit)**: Implement implicit triggers for table state changes.
    - [x] Update `SPECS.md` with `TABLE_STATE` protocol.
    - [x] Update `gm_persona.md` with instructions for `TABLE_STATE` block.
    - [x] Update `parser.py` to extract `TABLE_STATE`.
    - [x] Update `main.py` to handle detected state changes with a `StateChangeView`.
    - [x] Verify with tests and docs.
- [x] **Table State Machine**: Implement session phase and OOC vs IC state management to prevent meta-bleed.
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
