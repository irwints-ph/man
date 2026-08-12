import argparse
import os
import sys
from pathlib import Path

from .config import initialize_config, load_config, add_topic, delete_topic, resolve_path
from .reader import render_document

def main():
    parser = argparse.ArgumentParser(description="Manual/Documentation Reader")
    parser.add_argument("topic", nargs="?", help="The topic or command you want to read the manual for (e.g., pf, bv)")
    parser.add_argument("-l", "--list", action="store_true", help="List all available topics")
    parser.add_argument("-i", "--init", action="store_true", help="Initialize a new blank configuration file if one does not exist")
    parser.add_argument("-a", "--add", "-e", "--edit", nargs=2, metavar=("TOPIC", "PATH"), dest="add", help="Add or edit a manual page mapping (Provide an absolute path)")
    parser.add_argument("-d", "--delete", metavar="TOPIC", help="Delete a manual page mapping from the configuration")
    
    args = parser.parse_args()
    
    if args.init:
        initialize_config()
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
    
    doc_path = resolve_path(raw_path, config.get("sources", {}), root_dir)
        
    if not doc_path.exists():
        print(f"Error: Documentation file not found at {doc_path}")
        sys.exit(1)
        
    render_document(doc_path, topic)
