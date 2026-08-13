# 📄 Required Context Map — `man` Dependency Registry

---

# Metadata

| Field | Value |
|--------|-------|
| Document | `022-required-context-map.md` |
| Category | AFK Replay Framework |
| Type | Context Map & Dependency Registry |
| Status | 🟢 Active |
| Version | 1.0 |
| As Of | 2026-08-13 |

---

# 1. Environment & Installation

- **Root Directory**: `C:\Users\ErTSantos\Documents\_Codes\_Project\man`
- **Installation Command**: `pip install -e .`
- **Configuration File**: [`pyproject.toml`](file:///c:/Users/ErTSantos/Documents/_Codes/_Project/man/pyproject.toml)
- **Runtime Dependency**: `rich` library (`pip install rich`)

---

# 2. Key Codebase Components

| Component | Code File | Key Functions / Responsibilities |
| :--- | :--- | :--- |
| **CLI Router** | [`man/cli.py`](file:///c:/Users/ErTSantos/Documents/_Codes/_Project/man/man/cli.py) | `main()` - parses CLI arguments, routes `-r`, `-l`, `-a`, `-d`, `-i`, and topic lookups |
| **Config Engine** | [`man/config.py`](file:///c:/Users/ErTSantos/Documents/_Codes/_Project/man/man/config.py) | `load_config()`, `add_topic()`, `delete_topic()`, `resolve_path()` |
| **Document Reader** | [`man/reader.py`](file:///c:/Users/ErTSantos/Documents/_Codes/_Project/man/man/reader.py) | `render_document()` - renders Markdown using `rich` console & `less` pager |
| **Documentation** | [`readme.md`](file:///c:/Users/ErTSantos/Documents/_Codes/_Project/man/readme.md) | Technical guide and user instructions |
