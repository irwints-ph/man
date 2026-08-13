# 📄 Session Framework & Standards — `man`

---

# Metadata

| Field | Value |
|--------|-------|
| Document | `020-session-framework.md` |
| Category | AFK Replay Framework |
| Type | Workflow & Verification Guidelines |
| Status | 🟢 Active |
| Version | 1.0 |
| As Of | 2026-08-13 |

---

# 1. Operational Workflow Guidelines

1. **Lightweight CLI**: Keep startup fast and minimal. Avoid heavy imports until needed.
2. **Path Safety**: Ensure both relative and absolute paths resolve correctly on Windows and Unix environments.
3. **Graceful Fallbacks**: Fall back cleanly if `rich` is missing or `less.exe` is not installed on Windows.
4. **Verification**: Verify CLI commands via `--help` checks or running sample reads before completing tasks.
