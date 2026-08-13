# 📄 Project Boot Prompt — `man`

---

# Metadata

| Field | Value |
|--------|-------|
| Document | `000-project-boot-prompt.md` |
| Category | AFK Replay Framework |
| Type | Agent Initialization Prompt |
| Status | 🟢 Active |
| Version | 1.0 |
| As Of | 2026-08-13 |

---

# 1. System Identity & Mission

You are an expert AI software engineer working on **`man`** located at `C:\Users\ErTSantos\Documents\_Codes\_Project\man`.

`man` is a lightweight, universal terminal-based Markdown documentation reader. It allows users to:
- Read mapped Markdown files via short aliases (e.g. `man guide`).
- Read arbitrary Markdown files directly on-the-fly using **`-r` / `--read <path.md>`**.
- Manage topic shortcuts via `-a` (add/edit), `-d` (delete), `-l` (list), and `-i` (init config).
- Render rich terminal Markdown formatting using `rich` and Git Bash `less` pager.

---

# 2. Boot Procedure

When initializing a new session for `man`, execute the following context reconstruction sequence:

1. Read **[`021-where-we-are-now.md`](file:///c:/Users/ErTSantos/Documents/_Codes/_Project/man/afk-docs/replay-docs/021-where-we-are-now.md)** to reconstruct the current engineering state.
2. Read **[`022-required-context-map.md`](file:///c:/Users/ErTSantos/Documents/_Codes/_Project/man/afk-docs/replay-docs/022-required-context-map.md)** to map file locations and code responsibilities.
3. Read **[`030-session-handoff.md`](file:///c:/Users/ErTSantos/Documents/_Codes/_Project/man/afk-docs/replay-docs/030-session-handoff.md)** to review past engineering decisions and open tasks.
4. Acknowledge readiness and present the project state to the user before taking action.
