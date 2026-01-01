# Feedback Module Design

## 1. Overview
The Feedback Module captures, interprets, and stores player feedback ("Stars" for likes, "Wishes" for desires) to improve the GM's performance and campaign direction. It supports both explicit slash commands and implicit detection via the GM persona.

## 2. Public Interface

### Functions
- `record_feedback(feedback_type: str, user: str, message: str, interpretation: str) -> None`
  - Appends the feedback entry to `memory/feedback.ledger`.
- `get_feedback_interpretation(feedback_type: str, message: str) -> str`
  - Uses the `MODEL_FEEDBACK` (or GM model) to generate a concise interpretation and `FEEDBACK_UPDATE` block.

### Slash Commands
- `/stars [message]`: Submit positive feedback.
- `/wishes [message]`: Submit constructive feedback/desires.

### Protocols
- `FEEDBACK_DETECTED`: Output by the GM when it identifies implicit feedback in user messages.
  ```markdown
  ```FEEDBACK_DETECTED
  type: [star|wish]
  user: [username]
  content: [feedback text]
  ```
  ```

## 3. Data Structures

### `feedback.ledger`
A persistent log of all confirmed feedback.
```markdown
# Entry added on YYYY-MM-DD HH:MM:SS from user [Username]
- [Fact] Interpretation of the feedback...
```

## 4. Implicit Feedback Flow
1. **Detection**: The GM persona analyzes user input for strong sentiment or specific desires.
2. **Signal**: GM outputs a `FEEDBACK_DETECTED` block.
3. **Parsing**: The `parser` module extracts this block.
4. **Verification**: The system interprets the feedback using `get_feedback_interpretation` (optional, or uses the content from detection).
5. **Confirmation**: A `FeedbackConfirmView` is presented to the user.
6. **Storage**: Upon confirmation, `record_feedback` is called.
