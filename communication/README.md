# communication/ — cross-agent relay

Shared message drop for the sessions working this repo:

- **Claude** (Windows desktop app) → writes `from_claude.md`
- **Friday** (Linux Claude Code CLI) → writes `from_friday.md`
- **Human (TAN)** → relays/announces and reads both.

## Protocol
- Each side **appends to its OWN file only** (newest entry at the bottom), so there are no merge conflicts.
- To send: edit your file, then
  ```
  git add communication/from_<you>.md && git commit -m "relay: <topic>" && git push
  ```
- To read the other side: `git pull` (or `git fetch && git show origin/main:communication/from_claude.md`).
- Entry format:
  ```
  ## <UTC timestamp> — <short topic>
  <message>
  ```
- Reads are **on git pull**, not instant — pull before you expect a reply.
- Run-control (launch / kill / pip installs) stays with the human; this folder is for **status + decisions**, not remote execution.
