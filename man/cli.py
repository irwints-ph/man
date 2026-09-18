import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from .config import initialize_config, load_config, add_topic, delete_topic, resolve_path, resolve_source_and_file
from .reader import render_document


def open_in_mdp(source_dir: Path, rel_file: str = "", browser: str = "default"):
    """
    Launches mdp pointing to the topic's source directory and pre-selects the file.
    """
    mdp_cmd = shutil.which("mdp")
    cmd = []
    if mdp_cmd:
        cmd = [mdp_cmd, str(source_dir)]
    else:
        fallback_batch = Path(r"D:\sw\batch\mdp.cmd")
        if fallback_batch.exists():
            cmd = [str(fallback_batch), str(source_dir)]
        else:
            fallback_main = Path(r"D:\sw\batch\mdp\main.py")
            if fallback_main.exists():
                cmd = [sys.executable, str(fallback_main), str(source_dir)]
            else:
                print("Error: 'mdp' (Markdown Preview Pane) launcher not found in PATH or D:\\sw\\batch.")
                sys.exit(1)

    if rel_file:
        cmd.extend(["-f", rel_file])
    if browser and browser != "default":
        cmd.extend(["-b", browser])

    print(f"Launching mdp for source directory: {source_dir}")
    if rel_file:
        print(f"Opening document: {rel_file}")

    try:
        subprocess.run(cmd, check=False)
    except KeyboardInterrupt:
        pass


def main():
    parser = argparse.ArgumentParser(description="Manual/Documentation Reader")
    parser.add_argument("topic", nargs="?", help="The topic or command you want to read the manual for (e.g., pf, bv, bvt)")
    parser.add_argument("-b", "--browser", nargs="?", const="default", default=None, help="Open documentation in mdp (Markdown Preview Pane) web browser. Optional browser: chrome, edge, firefox, etc.")
    parser.add_argument("-r", "--read", metavar="PATH", help="Read a specific Markdown file directly without adding it to configuration")
    parser.add_argument("-l", "--list", action="store_true", help="List all available topics")
    parser.add_argument("-i", "--init", action="store_true", help="Initialize a new blank configuration file if one does not exist")
    parser.add_argument("-a", "--add", "-e", "--edit", nargs=2, metavar=("TOPIC", "PATH"), dest="add", help="Add or edit a manual page mapping (Provide an absolute path)")
    parser.add_argument("-d", "--delete", metavar="TOPIC", help="Delete a manual page mapping from the configuration")
    
    args = parser.parse_args()
    
    if args.init:
        initialize_config()
        sys.exit(0)

    if args.read:
        file_path = Path(args.read)
        if not file_path.is_absolute():
            file_path = Path(os.getcwd()) / args.read
            
        if not file_path.exists():
            print(f"Error: The file '{file_path}' does not exist.")
            sys.exit(1)
            
        if args.browser:
            open_in_mdp(file_path.parent, file_path.name, browser=args.browser)
            sys.exit(0)

        topic_display_name = file_path.stem
        render_document(file_path, topic_display_name)
        sys.exit(0)
    
    config = load_config()
            
    if args.add:
        topic_name, file_path = args.add
        topic_name = topic_name.lower()
        
        test_path = Path(file_path)
        if not test_path.is_absolute():
            test_path = Path(os.getcwd()) / file_path
            
        if not test_path.exists():
            print(f"Error: The file '{test_path}' does not exist.")
            sys.exit(1)
            
        add_topic(config, topic_name, test_path)
        sys.exit(0)
            
    if args.delete:
        topic_name = args.delete.lower()
        delete_topic(config, topic_name)
        sys.exit(0)
            
    if args.list or not args.topic:
        print("\nAvailable manual topics:")
        for key, path in config["topics"].items():
            resolved_path = path
            for k, v in config.get("sources", {}).items():
                if f"{{{k}}}" in resolved_path:
                    resolved_path = resolved_path.replace(f"{{{k}}}", v)
            print(f"  {key:<15} -> {resolved_path}")
        print("\nUsage: man <topic>")
        sys.exit(0)
        
    topic = args.topic.lower()
    if topic not in config["topics"]:
        print(f"Error: Topic '{topic}' not found in man_config.json")
        print("Run 'man --list' to see all available topics.")
        sys.exit(1)
        
    raw_path = config["topics"][topic]
    root_dir = Path(__file__).resolve().parent.parent
    
    source_dir, rel_file, doc_path = resolve_source_and_file(raw_path, config.get("sources", {}), root_dir)
        
    if not doc_path.exists():
        print(f"Error: Documentation file not found at {doc_path}")
        sys.exit(1)
        
    if args.browser:
        open_in_mdp(source_dir, rel_file, browser=args.browser)
        sys.exit(0)

    render_document(doc_path, topic)
