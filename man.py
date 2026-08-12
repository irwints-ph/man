import argparse
import json
import os
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Manual/Documentation Reader")
    parser.add_argument("topic", nargs="?", help="The topic or command you want to read the manual for (e.g., pf, bv)")
    parser.add_argument("-l", "--list", action="store_true", help="List all available topics")
    parser.add_argument("-i", "--init", action="store_true", help="Initialize a new blank configuration file if one does not exist")
    parser.add_argument("-a", "--add", "-e", "--edit", nargs=2, metavar=("TOPIC", "PATH"), dest="add", help="Add or edit a manual page mapping (Provide an absolute path)")
    parser.add_argument("-d", "--delete", metavar="TOPIC", help="Delete a manual page mapping from the configuration")
    
    args = parser.parse_args()
    
    root_dir = Path(__file__).resolve().parent
    config_file = root_dir / "man_config.json"
    
    if args.init:
        if config_file.exists():
            print(f"Configuration file already exists at {config_file}")
        else:
            docs_dir = str(root_dir / "docs").replace("\\", "/")
            initial_config = {
                "sources": {
                    "man-docs": docs_dir
                },
                "topics": {
                    "man": "{man-docs}/man-usage.md"
                }
            }
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(initial_config, f, indent=4)
            print(f"Successfully initialized new configuration file at {config_file}")
        sys.exit(0)
    
    if not config_file.exists():
        print(f"Error: Configuration file not found at {config_file}")
        print("Run 'man --init' to generate a new blank configuration file.")
        sys.exit(1)
        
    with open(config_file, "r", encoding="utf-8") as f:
        try:
            config = json.load(f)
            # Support auto-migration if the config is flat
            if "topics" not in config:
                config = {"sources": {}, "topics": config}
        except json.JSONDecodeError:
            print(f"Error: Failed to parse {config_file}")
            sys.exit(1)
            
    if args.add:
        topic_name, file_path = args.add
        topic_name = topic_name.lower()
        
        test_path = Path(file_path)
        if not test_path.is_absolute():
            # If it's relative, assume it's relative to the current working directory, not the script directory
            test_path = Path(os.getcwd()) / file_path
            
        if not test_path.exists():
            print(f"Error: The file '{test_path}' does not exist.")
            sys.exit(1)
            
        final_path = test_path.resolve().as_posix()
        compressed = False
        
        # Try to compress the path by replacing known source directories with their {alias}
        for src_key, src_val in config.get("sources", {}).items():
            src_val_norm = Path(src_val).resolve().as_posix()
            if final_path.lower().startswith(src_val_norm.lower()):
                final_path = f"{{{src_key}}}" + final_path[len(src_val_norm):]
                compressed = True
                break
                
        if not compressed:
            # Auto-generate a new source based on the topic name
            parent_dir = test_path.resolve().parent
            source_alias = f"{topic_name}-docs"
                
            # Ensure the alias is unique
            base_alias = source_alias
            counter = 1
            while source_alias in config.get("sources", {}):
                source_alias = f"{base_alias}-{counter}"
                counter += 1
                
            if "sources" not in config:
                config["sources"] = {}
            config["sources"][source_alias] = parent_dir.as_posix()
            
            # Compress using the newly generated source
            final_path = f"{{{source_alias}}}/{test_path.name}"
            print(f"Auto-created new source: '{source_alias}' -> {parent_dir.as_posix()}")
                
        config["topics"][topic_name] = final_path
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        print(f"Successfully added '{topic_name}' -> {final_path}")
        sys.exit(0)
            
    if args.delete:
        topic_name = args.delete.lower()
        if topic_name in config["topics"]:
            del config["topics"][topic_name]
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
            print(f"Successfully deleted '{topic_name}' from configuration.")
        else:
            print(f"Error: Topic '{topic_name}' not found.")
        sys.exit(0)
            
    if args.list or not args.topic:
        print("\nAvailable manual topics:")
        for key, path in config["topics"].items():
            resolved_path = path
            # Simple interpolation for list view
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
    # Resolve any {variable} templates in the path using sources
    for key, value in config.get("sources", {}).items():
        placeholder = f"{{{key}}}"
        if placeholder in raw_path:
            raw_path = raw_path.replace(placeholder, value)
            
    doc_path = Path(raw_path)
    if not doc_path.is_absolute():
        # Fallback for old configs that might still have relative paths
        doc_path = root_dir / config["topics"][topic]
        
    if not doc_path.exists():
        print(f"Error: Documentation file not found at {doc_path}")
        sys.exit(1)
        
    print(f"Preparing manual for '{topic}', please wait...")
        
    try:
        from rich.console import Console
        from rich.markdown import Markdown
    except ImportError:
        print("Error: The 'rich' library is required for advanced rendering. Run 'pip install rich' first.")
        sys.exit(1)
        
    with open(doc_path, "r", encoding="utf-8") as f:
        md_text = f.read()
        
    console = Console()
    md = Markdown(md_text)
    
    less_path = r"C:\Program Files\Git\usr\bin\less.exe"
    if os.path.exists(less_path):
        import ctypes
        buf = ctypes.create_unicode_buffer(512)
        ctypes.windll.kernel32.GetShortPathNameW(less_path, buf, 512)
        short_less_path = buf.value
        
        os.environ["PAGER"] = f"{short_less_path} -R"
    
    with console.pager(styles=True):
        console.print(f"\n--- Reading: {doc_path} ---\n", style="bold blue")
        console.print(md)
        console.print(f"\n--- End of {topic} ---\n", style="bold blue")

if __name__ == "__main__":    
    main()
