import json
import sys
from pathlib import Path

def get_config_path():
    # The config file lives in the parent directory (the root of the repo)
    root_dir = Path(__file__).resolve().parent.parent
    return root_dir / "man_config.json"

def initialize_config():
    config_file = get_config_path()
    if config_file.exists():
        print(f"Configuration file already exists at {config_file}")
    else:
        root_dir = config_file.parent
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

def load_config():
    config_file = get_config_path()
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
            return config
        except json.JSONDecodeError:
            print(f"Error: Failed to parse {config_file}")
            sys.exit(1)

def save_config(config):
    config_file = get_config_path()
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

def resolve_path(raw_path, sources, root_dir):
    # Resolve any {variable} templates in the path using sources
    for key, value in sources.items():
        placeholder = f"{{{key}}}"
        if placeholder in raw_path:
            raw_path = raw_path.replace(placeholder, value)
            
    doc_path = Path(raw_path)
    if not doc_path.is_absolute():
        doc_path = root_dir / raw_path
        
    return doc_path

def add_topic(config, topic_name, test_path):
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
    save_config(config)
    print(f"Successfully added '{topic_name}' -> {final_path}")
    
def delete_topic(config, topic_name):
    if topic_name in config["topics"]:
        del config["topics"][topic_name]
        save_config(config)
        print(f"Successfully deleted '{topic_name}' from configuration.")
    else:
        print(f"Error: Topic '{topic_name}' not found.")
