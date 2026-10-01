"""
Frontend Single Page Application (SPA) HTML/CSS/JS Loader for mdp.

Modular layout:
  mdp/web/
    ├── index.html        (Semantic DOM & CDN asset links)
    ├── css/
    │   ├── theme.css     (Design tokens, dark/light themes, typography, navbar)
    │   ├── layout.css    (2-pane flex container, sidebar, explorer tree, TOC)
    │   ├── markdown.css  (Reading canvas, code blocks, font zoom, GitHub alerts)
    │   ├── mermaid.css   (High-contrast actors, lifelines, loop boxes, arrows)
    │   └── lightbox.css  (Inspector modal, pan/zoom card canvas, toolbar)
    └── js/
        ├── ui.js         (Theme toggle, document font zoom, shortcuts)
        ├── explorer.js   (Tree model, recursive renderer, live search filter)
        ├── markdown.js   (Marked.js config, ABAP syntax, alerts, TOC generator)
        ├── viewer.js     (loadFiles, openFile, root-file priority, relative links)
        ├── lightbox.js   (Diagram enlarge, SVG viewBox math, wheel zoom, pan)
        └── heartbeat.js  (Watchdog heartbeat loop & beacon shutdown)
"""

from pathlib import Path
from typing import Optional

WEB_DIR = Path(__file__).resolve().parent / "web"
CSS_DIR = WEB_DIR / "css"
JS_DIR = WEB_DIR / "js"

# Ordered list of CSS modules
CSS_MODULES = [
    "theme.css",
    "layout.css",
    "markdown.css",
    "mermaid.css",
    "lightbox.css",
]

# Ordered list of JavaScript modules
JS_MODULES = [
    "ui.js",
    "explorer.js",
    "markdown.js",
    "viewer.js",
    "lightbox.js",
    "heartbeat.js",
]

_CACHED_TEMPLATE: Optional[str] = None


def build_template() -> str:
    """
    Reads index.html, all CSS modules, and all JS modules, assembling them
    into a standalone single-page HTML payload with zero runtime build dependencies.
    """
    index_file = WEB_DIR / "index.html"
    if not index_file.exists():
        raise FileNotFoundError(f"Frontend template not found at {index_file}")

    html = index_file.read_text(encoding="utf-8")

    # Combine CSS modules
    css_parts = []
    for mod in CSS_MODULES:
        mod_path = CSS_DIR / mod
        if mod_path.exists():
            css_parts.append(f"/* === [{mod}] === */\n" + mod_path.read_text(encoding="utf-8"))
        else:
            print(f"[MDP Warning] Missing CSS module: {mod_path}")
    combined_css = "\n\n".join(css_parts)

    # Combine JS modules
    js_parts = []
    for mod in JS_MODULES:
        mod_path = JS_DIR / mod
        if mod_path.exists():
            js_parts.append(f"// === [{mod}] ===\n" + mod_path.read_text(encoding="utf-8"))
        else:
            print(f"[MDP Warning] Missing JS module: {mod_path}")
    combined_js = "\n\n".join(js_parts)

    # Inject into placeholders
    html = html.replace("/* __INJECT_CSS__ */", combined_css)
    html = html.replace("/* __INJECT_JS__ */", combined_js)

    return html


def get_html_template(dev_mode: bool = True) -> str:
    """
    Returns the assembled HTML template.
    In dev_mode (default), re-reads web/ assets on every call so that CSS/JS edits
    take effect immediately upon browser refresh (F5) without restarting Python.
    """
    global _CACHED_TEMPLATE
    if not dev_mode and _CACHED_TEMPLATE is not None:
        return _CACHED_TEMPLATE

    template = build_template()
    if not dev_mode:
        _CACHED_TEMPLATE = template
    return template


# Exported constant for backward compatibility
try:
    HTML_TEMPLATE = get_html_template(dev_mode=False)
except Exception:
    HTML_TEMPLATE = ""
