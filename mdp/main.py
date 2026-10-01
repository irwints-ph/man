"""
Main CLI entry point for Markdown Preview Pane (mdp)
====================================================
Parses command line arguments, handles status queries and termination requests,
initializes the HTTP server, and launches the browser UI.
"""

import argparse
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

    # Resolve target directory (prioritizes explicit -d/--start-dir over positional directory)
    raw_dir_input = args.start_dir if args.start_dir else (args.directory or ".")
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
