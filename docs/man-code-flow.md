# 🔀 Code Execution Flows

This document outlines the execution path across the new multi-file architecture (`cli.py`, `config.py`, `reader.py`) for the core commands in the `man` utility.

---

## 1. Reading a Topic (`man <topic>`)

When a user requests to read a manual page, the flow is designed to safely load configurations, resolve variables, and stream the markdown to the pager.

```mermaid
sequenceDiagram
    participant CLI as cli.py
    participant Config as config.py
    participant Reader as reader.py
    
    CLI->>Config: load_config()
    Config-->>CLI: Return parsed JSON
    
    CLI->>CLI: Check if topic exists in config["topics"]
    
    CLI->>Config: resolve_path(raw_path, sources)
    Note over Config: Replace {source} variables
    Config-->>CLI: Return absolute Path object
    
    CLI->>Reader: render_document(doc_path, topic)
    Reader->>Reader: Check if Git 'less' pager exists
    Note over Reader: Parse Markdown with Rich
    Reader-->>CLI: Display UI to User
```

---

## 2. Initialization (`man -i` or `man --init`)

This command safely generates the underlying JSON infrastructure if it doesn't already exist.

```mermaid
sequenceDiagram
    participant CLI as cli.py
    participant Config as config.py
    
    CLI->>Config: initialize_config()
    Config->>Config: Check if man_config.json exists
    
    alt File exists
        Config-->>CLI: Print "File already exists"
    else File does not exist
        Config->>Config: Create initial dict with "man-docs" source
        Config->>Config: json.dump() to man_config.json
        Config-->>CLI: Print Success Message
    end
    
    CLI->>CLI: sys.exit(0)
```

---

## 3. Adding a Topic (`man -a <topic> <path>`)

The addition flow contains the most complex logic, handling path normalization, dynamic templating, and automatic source generation.

```mermaid
sequenceDiagram
    participant CLI as cli.py
    participant Config as config.py
    
    CLI->>Config: load_config()
    Config-->>CLI: Return parsed JSON
    
    CLI->>Config: add_topic(config, topic, path)
    
    Config->>Config: Normalize Path (resolve & as_posix)
    
    loop Over all known Sources
        Config->>Config: Check if new path starts with Source path
    end
    
    alt Match Found
        Config->>Config: Compress path using {source} alias
    else No Match Found
        Note over Config: Auto-generate Source Alias
        Config->>Config: Create unique alias (e.g. topic-docs)
        Config->>Config: Append new Source to config["sources"]
        Config->>Config: Compress path using new {topic-docs}
    end
    
    Config->>Config: save_config(config)
    Config-->>CLI: Print Success Message
```

---

## 4. Deleting a Topic (`man -d <topic>`)

A straightforward process to remove aliases safely.

```mermaid
sequenceDiagram
    participant CLI as cli.py
    participant Config as config.py
    
    CLI->>Config: load_config()
    Config-->>CLI: Return parsed JSON
    
    CLI->>Config: delete_topic(config, topic)
    
    alt Topic Exists
        Config->>Config: Remove from config["topics"]
        Config->>Config: save_config()
        Config-->>CLI: Print Success
    else Topic Missing
        Config-->>CLI: Print Error Message
    end
```
