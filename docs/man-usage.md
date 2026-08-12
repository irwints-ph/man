# 📖 Universal Manual Reader (`man`)

The `man` utility is a highly customizable, cross-project documentation reader for the terminal. It uses a centralized configuration file to alias markdown files across any directory into quick, accessible topics.

---

## 1. Quick Start & Navigation

To read a manual topic, simply type:
```bash
man <topic>
```
Example:
```bash
man pf
```

> [!TIP]
> The reader automatically attempts to use the `less` pager if it is installed on your system (e.g., via Git Bash).
> - Use the **Up/Down arrow keys** or **Mouse Scroll** to read through the document.
> - Press **`q`** to quit the reader and return to your terminal.

---

## 2. Managing Topics

### Listing Available Topics
To see all configured manuals and their resolved paths:
```bash
man --list
```
*(Or use the `-l` shortcut)*

### Adding or Editing a Topic
You can map a new alias directly from the terminal. 
*Note: You must provide an **absolute path** to the markdown file.*
```bash
man --add <topic> <absolute_path>
```
*(Or use `-a` or `-e`)*

Example:
```bash
man -a my-guide C:/Projects/docs/guide.md
```

### Deleting a Topic
To remove an alias from your configuration:
```bash
man --delete <topic>
```
*(Or use `-d`)*

---

## 3. Configuration & Sources (Advanced)

Under the hood, `man` reads from a `man_config.json` file located in the script's installation directory. 

For advanced users, you can manually edit this JSON file to create **Sources**. Sources allow you to define base directory paths and use them as variables to keep your config extremely clean.

### Example `man_config.json`
```json
{
    "sources": {
        "shared-docs": "C:/Projects/shared/docs"
    },
    "topics": {
        "guide1": "{shared-docs}/guide1.md",
        "guide2": "{shared-docs}/guide2.md"
    }
}
```

Whenever you use `man guide1`, the script will automatically resolve `{shared-docs}` and open the correct file!
