# 📄 Purpose & Scope — `man`

---

# Metadata

| Field | Value |
|--------|-------|
| Document | `010-purpose.md` |
| Category | AFK Replay Framework |
| Type | Strategic Purpose & Architectural Boundaries |
| Status | 🟢 Active |
| Version | 1.0 |
| As Of | 2026-08-13 |

---

# 1. Project Purpose

The primary objective of **`man`** is to provide a fast, elegant, terminal-native Markdown manual reader across Windows, Git Bash, PowerShell, and Command Prompt.

Instead of opening a browser or navigating deep folder structures to read project Markdown files (`.md`), `man` allows users to pull up formatted documentation directly in the console using simple aliases (e.g. `man pf`) or direct file paths (e.g. `man -r path/to/manual.md`).

---

# 2. Key System Capabilities

- **Topic Alias Mapping**: Mappings are stored in `man_config.json` linking short aliases to absolute or environment-resolved file paths.
- **Direct File Reading (`-r` / `--read`)**: Reads any `.md` file directly on-the-fly without requiring registration in `man_config.json`.
- **Rich Terminal Rendering**: Renders headers, lists, code blocks, bold text, and tables using `rich.markdown`.
- **Pager Integration**: Uses Git Bash `less.exe` pager (`PAGER="less -R"`) when available, enabling smooth arrow key and mouse scrolling.
- **CLI Options**:
  - `man <topic>`: Read mapped manual page.
  - `man -r <path.md>`: Read arbitrary Markdown file directly.
  - `man -l` / `--list`: List all registered topics.
  - `man -a <topic> <path>`: Add or edit a manual page mapping.
  - `man -d <topic>`: Delete a manual page mapping.
  - `man -i` / `--init`: Initialize default configuration.
