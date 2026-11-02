"""
Windows Context Menu Registry Manager for mdp
=============================================
Manages Explorer right-click integration ('Open with MDP') for folders,
folder backgrounds, and drive roots under HKEY_CURRENT_USER.
"""

from pathlib import Path
import os
import shutil
import sys

TARGET_KEYS = [
    r"Software\Classes\Directory\shell\Open with MDP",
    r"Software\Classes\Directory\Background\shell\Open with MDP",
    r"Software\Classes\Drive\shell\Open with MDP",
]
MENU_LABEL = "Open with MDP"


def find_pythonw_launcher() -> str:
    """Locate pythonw.exe interpreter for windowless background execution."""
    # 1. Check directory of current sys.executable
    if sys.executable:
        p = Path(sys.executable).parent / "pythonw.exe"
        if p.is_file():
            return str(p.resolve())

    # 2. Check virtualenvs
    user_home = Path.home()
    venv_candidates = [
        user_home / ".venv" / "video" / "Scripts" / "pythonw.exe",
        user_home / ".venv" / "pb8" / "Scripts" / "pythonw.exe",
    ]
    for c in venv_candidates:
        if c.is_file():
            return str(c.resolve())

    # 3. Check PATH
    which_w = shutil.which("pythonw.exe") or shutil.which("pythonw")
    if which_w:
        return str(Path(which_w).resolve())

    # 4. Fallback to sys.executable
    return sys.executable or "pythonw"


def find_mdp_launcher() -> str:
    """Locate the mdp.cmd or mdp launcher on the current system."""
    # 1. Search PATH for mdp.cmd, mdp.bat, mdp
    found = shutil.which("mdp.cmd") or shutil.which("mdp.bat") or shutil.which("mdp")
    if found and Path(found).suffix.lower() in (".cmd", ".bat", ".exe"):
        return str(Path(found).resolve())

    # 2. Well-known candidate locations
    candidates = [
        Path(r"D:\sw\batch\mdp.cmd"),
        Path(r"C:\sw\batch\mdp.cmd"),
        Path(r"D:\sw\mdp.cmd"),
        Path(r"C:\sw\mdp.cmd"),
    ]
    for c in candidates:
        if c.is_file():
            return str(c.resolve())

    # 3. Current executable or python entry point
    if sys.argv and sys.argv[0]:
        p = Path(sys.argv[0]).resolve()
        if p.suffix.lower() in (".cmd", ".bat"):
            return str(p)

    # 4. Fallback: command invoking python on mdp/main.py
    main_py = Path(__file__).resolve().parent / "main.py"
    py_exe = sys.executable or "python"
    return f'"{py_exe}" "{main_py}"'


def get_icon_path() -> str:
    """Returns a valid icon path for the context menu."""
    if sys.executable and os.path.isfile(sys.executable):
        return sys.executable
    return "shell32.dll,13"


def delete_key_recursive(root_key, subkey: str) -> bool:
    """Recursively deletes a Windows registry key and all its subkeys."""
    import winreg
    try:
        with winreg.OpenKey(root_key, subkey, 0, winreg.KEY_ALL_ACCESS) as key:
            while True:
                try:
                    sub = winreg.EnumKey(key, 0)
                    delete_key_recursive(key, sub)
                except OSError:
                    break
        winreg.DeleteKey(root_key, subkey)
        return True
    except (FileNotFoundError, OSError):
        return False


def register_context_menu(custom_launcher: str = None) -> bool:
    """Registers 'Open with MDP' in Windows Explorer right-click context menu (windowless background)."""
    if sys.platform != "win32":
        print("[ERROR] Context menu registration is only supported on Windows.")
        return False

    import winreg

    pythonw_exe = find_pythonw_launcher()
    main_py = str((Path(__file__).resolve().parent / "main.py").resolve())
    icon = pythonw_exe if os.path.isfile(pythonw_exe) else get_icon_path()

    # Windowless background execution command:
    # Invokes pythonw.exe directly so Windows does not create any console/cmd window.
    command_val = f'"{pythonw_exe}" "{main_py}" "%V"'

    print("=" * 60)
    print("  MDP Windows Context Menu Registration (-ro)")
    print("=" * 60)
    print(f"[*] Engine   : Windowless Background ({Path(pythonw_exe).name})")
    print(f"[*] Launcher : {pythonw_exe}")
    print(f"[*] Target   : {main_py}")
    print(f"[*] Command  : {command_val}")
    print(f"[*] Icon     : {icon}")
    print(f"[*] Label    : {MENU_LABEL}\n")

    success_count = 0
    for key_path in TARGET_KEYS:
        try:
            # Create shell key
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as k:
                winreg.SetValueEx(k, "", 0, winreg.REG_SZ, MENU_LABEL)
                if icon:
                    winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, icon)

            # Create command subkey
            cmd_key_path = rf"{key_path}\command"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, cmd_key_path) as k_cmd:
                winreg.SetValueEx(k_cmd, "", 0, winreg.REG_SZ, command_val)

            print(f"  [+] Registered: HKCU\\{key_path}")
            success_count += 1
        except Exception as e:
            print(f"  [-] Failed: HKCU\\{key_path} -> {e}")

    # Write backup mdp-open.reg in batch directory if possible
    try:
        batch_dir = Path(r"D:\sw\batch")
        if not batch_dir.is_dir():
            batch_dir = Path(__file__).resolve().parent.parent
        reg_file = batch_dir / "mdp-open.reg"
        escaped_pythonw = pythonw_exe.replace("\\", "\\\\")
        escaped_main_py = main_py.replace("\\", "\\\\")
        escaped_icon = icon.replace("\\", "\\\\")
        reg_content = (
            "Windows Registry Editor Version 5.00\n\n"
            f"[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\shell\\{MENU_LABEL}]\n"
            f'@="{MENU_LABEL}"\n'
            f'"Icon"="{escaped_icon}"\n\n'
            f"[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\shell\\{MENU_LABEL}\\command]\n"
            f'@="\\"{escaped_pythonw}\\" \\"{escaped_main_py}\\" \\"%V\\""\n\n'
            f"[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\Background\\shell\\{MENU_LABEL}]\n"
            f'@="{MENU_LABEL}"\n'
            f'"Icon"="{escaped_icon}"\n\n'
            f"[HKEY_CURRENT_USER\\Software\\Classes\\Directory\\Background\\shell\\{MENU_LABEL}\\command]\n"
            f'@="\\"{escaped_pythonw}\\" \\"{escaped_main_py}\\" \\"%V\\""\n\n'
            f"[HKEY_CURRENT_USER\\Software\\Classes\\Drive\\shell\\{MENU_LABEL}]\n"
            f'@="{MENU_LABEL}"\n'
            f'"Icon"="{escaped_icon}"\n\n'
            f"[HKEY_CURRENT_USER\\Software\\Classes\\Drive\\shell\\{MENU_LABEL}\\command]\n"
            f'@="\\"{escaped_pythonw}\\" \\"{escaped_main_py}\\" \\"%V\\""\n'
        )
        reg_file.write_text(reg_content, encoding="utf-8")
        print(f"\n[+] Created backup registration file: {reg_file}")
    except Exception:
        pass

    if success_count > 0:
        print("\n[SUCCESS] 'Open with MDP' context menu option added successfully!")
        print("          Runs silently in the background (no cmd window).")
        print("          Right-click any folder or folder background in Explorer to try it.")
        return True
    return False


def remove_context_menu() -> bool:
    """Removes 'Open with MDP' from Windows Explorer right-click context menu."""
    if sys.platform != "win32":
        print("[ERROR] Context menu operations are only supported on Windows.")
        return False

    import winreg

    print("=" * 60)
    print("  MDP Windows Context Menu Removal (-rro)")
    print("=" * 60)

    removed = 0
    for key_path in TARGET_KEYS:
        ok = delete_key_recursive(winreg.HKEY_CURRENT_USER, key_path)
        if ok:
            print(f"  [-] Removed: HKCU\\{key_path}")
            removed += 1
        else:
            print(f"  [.] Not present: HKCU\\{key_path}")

    if removed > 0:
        print(f"\n[SUCCESS] Removed 'Open with MDP' registry entries ({removed} keys cleaned).")
        return True
    else:
        print("\n[INFO] No 'Open with MDP' registry entries were found to remove.")
        return True
