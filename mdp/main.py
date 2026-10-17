"""
Main CLI entry point for Markdown Preview Pane (mdp)
====================================================
Parses command line arguments, handles status queries and termination requests,
initializes the HTTP server, and launches the browser UI.
"""

import argparse
import json
import os
import socketserver
import sys
import threading
import time
import urllib.parse
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

if sys.version_info < (3, 8):
    print(f"[ERROR] mdp requires Python 3.8 or higher. (Detected: {sys.version})")
    sys.exit(1)

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from mdp.process import DEFAULT_PORT, find_free_port, check_status, kill_instances
    from mdp.browser import open_browser
    from mdp.server import MarkdownPreviewHandler, start_watchdog
else:
    from .process import DEFAULT_PORT, find_free_port, check_status, kill_instances
    from .browser import open_browser
    from .server import MarkdownPreviewHandler, start_watchdog


def register_to_man(topic_name="mdp", target_file="", target_dir=None):
    """
    Registers a manual topic into man's configuration (man_config.json).
    Defaults to registering mdp's own manual (docs/mdp.md).
    """
    repo_root = Path(__file__).resolve().parent.parent
    if topic_name.lower() == "mdp" and not target_file:
        doc_path = repo_root / "docs" / "mdp.md"
        if not doc_path.exists():
            doc_path = Path(r"D:\sw\batch\docs\mdp.md")
    else:
        if target_file:
            doc_path = Path(target_file).resolve()
        elif target_dir:
            td = Path(target_dir).resolve()
            candidates = [td / f"{topic_name}.md", td / "README.md", td / "readme.md"]
            doc_path = next((c for c in candidates if c.exists()), None)
            if not doc_path:
                print(f"[ERROR] Could not find markdown documentation for '{topic_name}' in {td}")
                return
        else:
            candidates = [Path(f"{topic_name}.md"), Path("README.md"), Path("readme.md")]
            doc_path = next((c for c in candidates if c.exists()), None)
            if not doc_path:
                print(f"[ERROR] Could not find markdown documentation for '{topic_name}' in current directory.")
                return

    if not doc_path or not doc_path.exists():
        print(f"[ERROR] Manual documentation file not found at: {doc_path}")
        return

    print("=" * 60)
    print(f"  [MDP] Registering '{topic_name}' into Universal Manual Reader (man)")
    print("=" * 60)
    print(f"  Documentation : {doc_path}")

    # 1. Direct integration with man.config
    try:
        sys.path.insert(0, str(repo_root))
        from man.config import load_config, add_topic
        config = load_config()
        add_topic(config, topic_name, doc_path)
        print(f"\n  [SUCCESS] '{topic_name}' has been added to man!")
        print(f"  - Terminal view : man {topic_name}")
        print(f"  - Browser view  : man {topic_name} -b")
        print("=" * 60)
        return
    except Exception:
        pass

    # 2. CLI fallback (man -a topic_name doc_path)
    import shutil
    import subprocess
    man_cmd = shutil.which("man")
    if not man_cmd:
        fallback_bat = Path(r"D:\sw\batch\man.cmd")
        if fallback_bat.exists():
            man_cmd = str(fallback_bat)

    if man_cmd:
        try:
            subprocess.run([man_cmd, "-a", topic_name, str(doc_path)], check=True)
            print(f"\n  [SUCCESS] '{topic_name}' registered via man CLI!")
            print(f"  - Terminal view : man {topic_name}")
            print(f"  - Browser view  : man {topic_name} -b")
            print("=" * 60)
            return
        except Exception as err:
            print(f"[ERROR] Failed to run '{man_cmd} -a': {err}")

    print("[ERROR] Could not locate 'man' package or CLI to register topic.")


def find_code_locations_file():
    """
    Locates code-locations.json using environment variable or standard locations.
    """
    env_file = os.environ.get("CODE_LOCATIONS_FILE")
    if env_file:
        p = Path(env_file)
        if p.is_file():
            return p

    candidates = [
        Path(r"D:\sw\batch\code-tools\code-locations.json"),
        Path(r"C:\sw\batch\code-tools\code-locations.json"),
        Path(__file__).resolve().parent.parent.parent / "sw" / "batch" / "code-tools" / "code-locations.json",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def load_code_applications(config_path):
    """
    Loads and normalizes all application entries and directoryAliases from code-locations.json.
    """
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    ws_root = data.get("workspaceRoot") or os.environ.get("WORKSPACE_DIR") or r"D:\_codes\_projects"
    lookup = {}
    canonical = []

    # Parse applications
    apps = data.get("applications", {})
    for key, app in apps.items():
        norm_key = key.strip().lower()
        name = app.get("name", norm_key)
        desc = app.get("description", name)
        raw_dir = app.get("directory", "")

        # Check environment variable overrides
        env_vars = app.get("environmentVariables", {})
        dir_env = env_vars.get("directory")
        if dir_env and os.environ.get(dir_env):
            raw_dir = os.environ[dir_env]

        raw_dir = raw_dir.replace("${workspaceRoot}", ws_root)
        resolved_path = Path(raw_dir)
        aliases = [a.strip().lower() for a in app.get("aliases", []) if a.strip()]

        entry = {
            "key": norm_key,
            "name": name,
            "description": desc,
            "path": resolved_path,
            "aliases": aliases
        }
        canonical.append(entry)
        lookup[norm_key] = entry
        for alias in aliases:
            lookup[alias] = entry

    # Parse directoryAliases
    dir_aliases = data.get("directoryAliases", {})
    for da_key, da in dir_aliases.items():
        norm_key = da_key.strip().lower()
        name = da.get("name", norm_key)
        raw_dir = da.get("directory", "").replace("${workspaceRoot}", ws_root)
        resolved_path = Path(raw_dir)
        aliases = [a.strip().lower() for a in da.get("aliases", []) if a.strip()]

        entry = {
            "key": norm_key,
            "name": name,
            "description": name,
            "path": resolved_path,
            "aliases": aliases
        }
        canonical.append(entry)
        lookup[norm_key] = entry
        for alias in aliases:
            lookup[alias] = entry

    return {"lookup": lookup, "canonical": canonical}


def list_code_applications():
    """
    Displays all available applications and their directory locations.
    """
    loc_file = find_code_locations_file()
    if not loc_file:
        print("[ERROR] code-locations.json not found.")
        return

    try:
        reg = load_code_applications(loc_file)
    except Exception as e:
        print(f"[ERROR] Failed to read code-locations.json: {e}")
        return

    print("=" * 65)
    print("  Available Application Targets (code-locations.json)")
    print("=" * 65)
    for entry in reg["canonical"]:
        alias_str = f" ({', '.join(entry['aliases'])})" if entry["aliases"] else ""
        exists_str = "" if entry["path"].exists() else " [NOT FOUND]"
        header = f"  - {entry['key']}{alias_str}"
        print(f"{header:<32} {entry['description']}{exists_str}")
        print(f"    Path: {entry['path']}")
    print("=" * 65)
    print("  Usage: mdp -a <name> [options]\n")


def resolve_application_directory(app_query):
    """
    Resolves an application name or alias to its absolute directory Path.
    """
    q = app_query.strip().lower()
    if q in ("?", "help", "list", "all"):
        list_code_applications()
        sys.exit(0)

    config_path = find_code_locations_file()
    if not config_path:
        print("[ERROR] code-locations.json not found.")
        return None

    try:
        reg = load_code_applications(config_path)
    except Exception as e:
        print(f"[ERROR] Failed to load code-locations.json: {e}")
        return None

    if q not in reg["lookup"]:
        print(f"\n[ERROR] Application '{app_query}' not found in code-locations.json.")
        print("\nAvailable applications:")
        for entry in reg["canonical"]:
            aliases_txt = f" ({', '.join(entry['aliases'])})" if entry["aliases"] else ""
            print(f"  - {entry['key']}{aliases_txt}")
        print("\nRun 'mdp -la' to see full application details.\n")
        return None

    entry = reg["lookup"][q]
    target_dir = entry["path"]
    if not target_dir.exists():
        print(f"\n[ERROR] Target directory for application '{app_query}' does not exist on disk:")
        print(f"       {target_dir}\n")
        return None

    print(f"[*] Target Application: {entry['name']} ({entry['key']}) -> {target_dir}")
    return target_dir


def main():
    parser = argparse.ArgumentParser(
        description="Markdown Preview Pane: Fast local two-pane Markdown browser."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=None,
        help="Directory to scan for .md files (default: . = directory where executed)."
    )
    parser.add_argument(
        "-a", "--app",
        type=str,
        default=None,
        metavar="APP",
        help="Target application from code-locations.json (e.g., -a balik, -a hub, -a supplier)."
    )
    parser.add_argument(
        "-la", "--list-apps",
        action="store_true",
        help="List all available applications registered in code-locations.json."
    )
    parser.add_argument(
        "-d", "--dir", "--directory", "--start-dir",
        dest="start_dir",
        type=str,
        default=None,
        help="Explicit start directory to scan for .md files (overrides positional directory)."
    )
    parser.add_argument(
        "-s", "--status",
        action="store_true",
        help="Check status of currently running mdp instances."
    )
    parser.add_argument(
        "-k", "--kill",
        action="store_true",
        help="Stop/kill running mdp instance(s)."
    )
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=0,
        help=f"Port to bind to (default: auto-select starting from {DEFAULT_PORT})."
    )
    parser.add_argument(
        "-b", "--browser",
        type=str,
        default="default",
        choices=["default", "chrome", "edge", "msedge", "firefox", "brave", "c", "e", "f", "b"],
        help="Specify which browser to open (default, chrome, edge, firefox, brave)."
    )
    parser.add_argument(
        "-f", "--file",
        type=str,
        default="",
        help="Initial markdown file (relative path or filename) to open/preview on startup."
    )
    parser.add_argument(
        "-e", "--expand",
        action="store_true",
        help="Expand all folders in the explorer tree by default (default: collapsed)."
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not open browser automatically."
    )
    parser.add_argument(
        "--keep-alive",
        action="store_true",
        help="Keep server running even after browser tab/window is closed."
    )
    parser.add_argument(
        "-ah", "--add-help",
        nargs="?",
        const="mdp",
        default=None,
        metavar="TOPIC",
        help="Automatically register mdp's manual (or specified topic) into man (equivalent to: man -a mdp <doc-path>)."
    )

    args = parser.parse_args()

    # Handle add-help flag (-ah)
    if args.add_help is not None:
        register_to_man(
            topic_name=args.add_help,
            target_file=args.file,
            target_dir=args.start_dir or args.directory
        )
        return

    # Handle status flag
    if args.status:
        check_status()
        return

    # Handle kill flag
    if args.kill:
        kill_instances(target_port=args.port)
        return

    # Handle list-apps flag (-la)
    if args.list_apps:
        list_code_applications()
        return

    # Resolve target directory from application flag (-a / --app)
    app_target_dir = None
    if args.app:
        app_target_dir = resolve_application_directory(args.app)
        if not app_target_dir:
            sys.exit(1)

    # Resolve target directory (prioritizes explicit -d/--start-dir, then -a, then positional directory)
    if args.start_dir:
        raw_dir_input = args.start_dir
    elif app_target_dir:
        if args.directory:
            candidate = app_target_dir / args.directory
            if candidate.exists():
                raw_dir_input = str(candidate)
            else:
                raw_dir_input = str(app_target_dir)
        else:
            raw_dir_input = str(app_target_dir)
    elif args.directory:
        raw_dir_input = args.directory
    else:
        raw_dir_input = "."
    dir_str = raw_dir_input.strip(' "\'')
    if dir_str.endswith('\\"') or dir_str.endswith('"'):
        dir_str = dir_str[:-1].rstrip('\\')
    if not dir_str:
        dir_str = "."

    raw_dir = Path(dir_str)
    if not raw_dir.exists():
        print(f"Error: Directory '{raw_dir}' does not exist.")
        sys.exit(1)

    target_path = raw_dir.resolve()
    initial_file = args.file.strip() if args.file else ""

    # If the user passed a specific markdown file directly as the directory target
    if target_path.is_file():
        if not initial_file:
            initial_file = target_path.name
        target_path = target_path.parent

    port = args.port if args.port > 0 else find_free_port(DEFAULT_PORT)

    MarkdownPreviewHandler.target_dir = target_path
    MarkdownPreviewHandler.start_time = time.time()
    MarkdownPreviewHandler.default_expand = args.expand

    server = socketserver.TCPServer(("127.0.0.1", port), MarkdownPreviewHandler)
    MarkdownPreviewHandler.server_instance = server
    MarkdownPreviewHandler.keep_alive = args.keep_alive
    MarkdownPreviewHandler.last_heartbeat = time.time()

    url = f"http://localhost:{port}"
    query_parts = []
    if initial_file:
        query_parts.append(f"file={urllib.parse.quote(initial_file.replace('\\', '/'))}")
    if args.expand:
        query_parts.append("expand=1")

    query_str = ("?" + "&".join(query_parts)) if query_parts else ""
    browser_url = f"{url}{query_str}"

    print("=" * 60)
    print("  [MDP] Markdown Preview Pane Server")
    print("=" * 60)
    print(f"  Target Directory : {target_path}")
    if initial_file:
        print(f"  Initial Document : {initial_file}")
    print(f"  Local Address    : {url}")
    print(f"  Browser Target   : {args.browser}")
    print(f"  Heartbeat Watchdog: Active (auto-closes when tab is closed)")
    print("=" * 60)
    print("  Press Ctrl+C to stop the server.\n")

    start_watchdog(server)

    if not args.no_browser:
        open_browser(browser_url, browser_name=args.browser)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping mdp server...")
    finally:
        server.server_close()
        print("Server stopped.")


if __name__ == "__main__":
    main()
