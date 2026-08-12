# 📖 Universal Manual Reader (`man`)

A lightweight, powerful, and universally accessible terminal-based reader for your Markdown documentation. 

Instead of digging through complex folder structures or opening a web browser to read your project's `.md` files, `man` lets you instantly pull up beautifully formatted documentation directly in your terminal using simple, memorable aliases (e.g., `man guide`).

---

## 🎯 What is it for?

If you maintain multiple code repositories, scripts, or personal knowledge bases, you likely have Markdown (`.md`) files scattered everywhere. 

`man` acts as a central switchboard. You register your Markdown files once, and `man` allows you to read them from anywhere on your computer. It fully renders Markdown (including tables, bold text, and headers) directly in the console, providing a seamless "man page" experience native to Linux/Unix, but built for modern workflows and Windows/Git Bash.

---

## 📋 Requirements

To run `man`, your system needs:
1. **Python 3.9+** installed on your system.
2. (Optional but Recommended) **Git for Windows (Git Bash)** - If installed, `man` will automatically detect and use the `less` pager, allowing you to scroll through long documents smoothly using your arrow keys or mouse wheel.

*Note: You do not need to be a Python developer to use this tool!*

---

## 🚀 Installation

> [!TIP]
> **Virtual Environment Recommended:** We highly recommend installing this in a Python Virtual Environment (`venv`) rather than your global system. Running the tool from within an active virtual environment is often faster!

1. Open your terminal (Command Prompt, PowerShell, or Git Bash).
2. Navigate to the folder where you downloaded this project:
   ```bash
   cd C:\Users\<yourusername>\Documents\_Codes\_Project\man
   ```
3. Create a new virtual environment named `.venv` inside the folder:
   ```bash
   python -m venv .venv
   ```
4. Activate the virtual environment (Run the command that matches your terminal):
   - **Command Prompt:** `.venv\Scripts\activate.bat`
   - **PowerShell:** `.venv\Scripts\Activate.ps1`
   - **Git Bash:** `source .venv/Scripts/activate`
5. Upgrade `pip` to the latest version:
   ```bash
   python -m pip install --upgrade pip
   ```
6. Install the tool using pip:
   ```bash
   pip install -e .
   ```
   *(This command installs the tool and automatically pulls in the `rich` library used to make the terminal text look beautiful. Note that the `-e` flag means it links directly to this folder, so don't delete the folder after installing!)*

---

## 🛠️ Initial Usage (First-Time Setup)

Once installed, you can run the tool from **any folder on your computer**.

If this is your first time using it, you need to initialize the configuration file. Run:
```bash
man --init
```
*You will see a message confirming the configuration was generated. As a bonus, this command automatically registers the manual for the tool itself!*

To test that everything works, type:
```bash
man man
```
*(This will open the usage guide for the `man` tool itself. Press `q` on your keyboard to exit the reader).*

---

## 📚 Adding Your Own Documents (Beginner Guide)

You can easily link your own Markdown files to the reader so you can access them instantly.

### Step 1: Find your Markdown file
Let's say you have a file located at `C:\Projects\my-notes\how-to-code.md`.

### Step 2: Pick a short name (Topic)
Choose a short, easy-to-remember name for it. Let's use `coding`.

### Step 3: Add it to the reader
Run the following command in your terminal (`-a` stands for Add):
```bash
man -a coding C:\Projects\my-notes\how-to-code.md
```

### Step 4: Read it anytime!
Now, no matter what folder you are in, you can instantly read your notes by typing:
```bash
man coding
```

---

## ⚙️ Advanced Commands Reference

If you forget what topics you have saved, you can list them all:
```bash
man --list
```

If you ever want to delete a topic (this does **not** delete your actual Markdown file, just the shortcut):
```bash
man --delete coding
```

If you move a file and need to update the shortcut, just add it again. It will overwrite the old path:
```bash
man -a coding C:\NewFolder\how-to-code.md
```

---

## 🛠️ Alternative Installation (Batch File & PATH)

If `pip install -e .` doesn't work for you, or if you prefer manual configuration, you can make `man` available everywhere on your system by creating a simple batch file and updating your User PATH (which requires **no admin privileges**).

### Step 1: Create a Batch File
1. Open Notepad.
2. Paste the following two lines (adjust the path if you downloaded the folder somewhere else):
   ```bat
   @echo off
   python C:\Users\<yourusername>\Documents\_Codes\_Project\man\man.py %*
   ```
3. Save the file as `man.bat`. We recommend saving it right inside the `man` project folder so everything stays together.

### Step 2: Add to your PATH
To use the `man` command from anywhere, you need to tell Windows where that `.bat` file lives.
1. Click the Windows Start menu and search for **"Environment Variables"**.
2. Select **"Edit environment variables for your account"** *(This is the non-admin option)*.
3. In the top window (User variables), find the variable named **`Path`** and click **Edit**.
4. Click **New** and paste the folder path where you saved `man.bat` (e.g., `C:\Users\<yourusername>\Documents\_Codes\_Project\man`).
5. Click **OK** on all windows to save.

### Step 3: Restart your Terminal
Close any open terminal windows (Command Prompt, Git Bash, etc.) and open a fresh one. You can now type `man` from anywhere!
