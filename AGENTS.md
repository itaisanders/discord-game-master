# AGENTS.md - Agent Workflow & Guidelines

> **Last Updated**: 2025-12-31
> **For**: AI agents working on this codebase

---

## 1. Orientation

You are working on the **Discord RPG Game Master Bot**.
*   **Architecture**: See [ARCHITECTURE.md](./ARCHITECTURE.md) for high-level design and core patterns.
*   **Specifications**: See [SPECS.md](./SPECS.md) for protocols, feature details, and constraints.
*   **Vision**: See [ROADMAP.md](./ROADMAP.md) for the "North Star" and future plans.

## 2. Operational Protocol: The "Document-Act" Loop

**Strictly follow this sequence for every task:**

1.  **Think & Plan**: Analyze the request. Update/Create `task.md` with a breakdown.
2.  **Verify Plan**: Wait for user approval of the plan (if complex).
3.  **Document**: Before writing code, update the relevant documentation (`SPECS.md`, `ARCHITECTURE.md`, module `DESIGN.md`). **WAIT for user review of docs.**
4.  **Act**: Execute the code/terminal commands only after documentation is approved.
5.  **Verify**: Run tests. Compare final output against usage in `SPECS.md`.

## 3. Development Workflow

### Prerequisite Checks
Before starting work, read:
*   `task.md` (Current objective)
*   `ARCHITECTURE.md` (To match patterns)
*   `SPECS.md` (To strict adhered to protocols)

### Testing Standards
*   **Run All Tests**: `pytest`
*   **New Features**: Must have accompanying tests in `tests/`.
*   **Async Mocking**: Use `AsyncMock` for `discord` and `genai` calls.

### Documentation Maintenance
*   **Pruning**: When moving content, delete it from the old location to avoid duplication.
*   **Links**: Ensure all relative links between `.md` files are valid.

## 4. Module Guides
Specific design documentation for sub-modules:
*   [Personas Design](./personas/DESIGN.md)
*   [Memory/Ledger Design](./memory/DESIGN.md)
*   [Scripts/Ingestion Design](./scripts/DESIGN.md)

---
**This document ensures all Agents operate with the same context and standards. When in doubt, check ARCHITECTURE.md.**
