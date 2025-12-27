# 📋 Active Task Tracking

This file tracks the current active development, bug fixes, and feature requests for the **Discord RPG Game Master Bot**.

---

## 🚀 Active Tasks

### Refactor Character Sheet Retrieval (Pending Approval)
**Objective**: Replace the slow and unreliable AI-based character sheet retrieval with a fast, deterministic parsing strategy to improve the performance of the `/sheet` command.

**Plan**:
- [ ] **1. One-Time Ledger Migration:** Create and run a temporary script that uses a purpose-built AI persona to read the existing `memory/party.ledger` and rewrite it into the new, structured format. This ensures existing data is not broken.
- [ ] **2. Update Memory Persona:** Modify `personas/memory_architect_persona.md` to instruct the AI to wrap each character's data in `party.ledger` within a unique, parsable block (e.g., ```` ```character_sheet[char_name=NAME]...``` ````) for all future updates.
- [ ] **3. Refactor `fetch_character_sheet`:** Rewrite the `fetch_character_sheet` function in `bot.py` to use a regular expression to parse `party.ledger` and extract the relevant character block, removing the live AI call.
- [ ] **4. Verify `get_character_name`:** Ensure the `get_character_name` function in `bot.py` remains compatible with the new ledger structure.
- [ ] **5. Update Documentation:** Modify `AGENTS.md` to document the new deterministic retrieval pattern and remove references to the old AI-extraction method.
- [ ] **6. Cleanup:** Delete the obsolete `personas/sheet_extractor_persona.md` and the temporary migration script.

---

## ✅ Completed Tasks

### Implement Native Slash Commands (Completed: 2025-12-27)
**Objective**: Convert all player-facing commands defined in `personas/gm_persona.md` from implicit text-based commands into explicit, native Discord slash commands. This improved user experience, reliability, and discoverability.

---

## 🛠️ Operational Protocol
1.  **Selection**: Choose a task from the **Active Tasks** or **Backlog**.
2.  **Planning**: Use Planning Mode to draft an implementation plan.
3.  **Execution**: Implement the changes and update the task status in this file.
4.  **Verification**: Run `pytest tests/` before marking a task as complete.
5.  **Completion**: Move the task to the **Completed Tasks** section with a timestamp.

> See [AGENTS.md](./AGENTS.md) for detailed architectural patterns and coding standards.
