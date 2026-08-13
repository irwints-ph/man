# 📄 Session Handoff — `man`

---

# Metadata

| Field | Value |
|--------|-------|
| Document | `030-session-handoff.md` |
| Category | AFK Replay Framework |
| Type | Session Handoff & Decision Record |
| Status | 🟢 Active |
| Version | 1.0 |
| As Of | 2026-08-13 |

---

# 1. Session Overview

This engineering session refactored **`man`** located at `C:\Users\ErTSantos\Documents\_Codes\_Project\man`:
1. Added **`-r` / `--read <path.md>`** option in [`man/cli.py`](file:///c:/Users/ErTSantos/Documents/_Codes/_Project/man/man/cli.py#L12-L35) to allow reading any Markdown file directly without adding it to `man_config.json`.
2. Updated [`readme.md`](file:///c:/Users/ErTSantos/Documents/_Codes/_Project/man/readme.md#L109-L116) with documentation and examples for `man -r <path.md>`.
3. Created full canonical 6-document AFK Replay Framework in [`afk-docs/replay-docs/`](file:///c:/Users/ErTSantos/Documents/_Codes/_Project/man/afk-docs/replay-docs/).

---

# 2. Engineering Decisions Record

### Decision 1: Direct File Reading (`-r` / `--read`) Option
- **Context**: Users wanted a way to open and read arbitrary Markdown files (e.g. project manuals, scratch notes) using `man` without having to register a shortcut alias via `man -a`.
- **Decision**: Added `-r` / `--read` parameter to `man/cli.py`. If specified, resolves the path (absolute or relative to current directory), checks file existence, extracts the stem name as topic title, and renders it directly via `render_document()`.
- **Rationale**: Provides instant on-the-fly terminal Markdown reading capability for any file.

---

# 3. Open Tasks & Next Steps

1. **Testing**: Test `man -r` on various `.md` manual pages across different workspace paths.
