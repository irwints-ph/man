"""
HTTP Server and Watchdog Handler module for mdp
===============================================
Handles local HTTP requests, JSON API endpoints (/api/files, /api/content,
/api/status, /api/heartbeat, /api/shutdown), and browser disconnection watchdog.
"""

import http.server
import json
import mimetypes
import os
import sys
import threading
import time
import urllib.parse
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from mdp.template import HTML_TEMPLATE, get_html_template
else:
    from .template import HTML_TEMPLATE, get_html_template


DEFAULT_EXTENSIONS = {
    ".md", ".markdown",
    ".sql",
    ".py",
    ".json",
    ".txt",
    ".csv",
    ".tsv",
    ".yaml", ".yml",
    ".sh", ".bat", ".cmd",
    ".ps1", ".psm1", ".psd1",
    ".js", ".ts",
    ".html", ".htm", ".css",
}


class MarkdownPreviewHandler(http.server.BaseHTTPRequestHandler):
    target_dir: Path = Path.cwd()
    server_instance = None
    has_connected: bool = False
    last_heartbeat: float = 0.0
    shutdown_timer: threading.Timer = None
    shutdown_lock = threading.Lock()
    keep_alive: bool = False
    start_time: float = 0.0
    default_expand: bool = False
    allowed_extensions = None

    @classmethod
    def record_heartbeat(cls):
        with cls.shutdown_lock:
            cls.has_connected = True
            cls.last_heartbeat = time.time()
            if cls.shutdown_timer and cls.shutdown_timer.is_alive():
                cls.shutdown_timer.cancel()
                cls.shutdown_timer = None

    @classmethod
    def request_shutdown(cls, delay=2.5):
        if cls.keep_alive:
            return
        with cls.shutdown_lock:
            if cls.shutdown_timer and cls.shutdown_timer.is_alive():
                cls.shutdown_timer.cancel()
            cls.shutdown_timer = threading.Timer(delay, cls.perform_shutdown)
            cls.shutdown_timer.daemon = True
            cls.shutdown_timer.start()

    @classmethod
    def perform_shutdown(cls):
        print("\nShutting down mdp server. Goodbye!")
        if cls.server_instance:
            threading.Thread(target=cls.server_instance.shutdown, daemon=True).start()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/heartbeat":
            MarkdownPreviewHandler.record_heartbeat()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"alive"}')
            return

        if path == "/api/shutdown":
            MarkdownPreviewHandler.request_shutdown()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"shutting_down"}')
            return

        self.send_error(404, "Not Found")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            try:
                html_bytes = get_html_template().encode("utf-8")
            except Exception:
                html_bytes = HTML_TEMPLATE.encode("utf-8")
            self.wfile.write(html_bytes)
            return

        if path == "/index.html":
            # If project has its own index.html, fall through to static handler
            user_index = self.target_dir / "index.html"
            if not user_index.is_file():
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                try:
                    html_bytes = get_html_template().encode("utf-8")
                except Exception:
                    html_bytes = HTML_TEMPLATE.encode("utf-8")
                self.wfile.write(html_bytes)
                return

        if path == "/api/status":
            info = {
                "status": "running",
                "pid": os.getpid(),
                "target_dir": str(self.target_dir),
                "uptime_seconds": int(time.time() - self.start_time) if self.start_time else 0,
                "keep_alive": self.keep_alive
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(json.dumps(info).encode("utf-8"))
            return

        if path == "/api/heartbeat":
            MarkdownPreviewHandler.record_heartbeat()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"alive"}')
            return

        if path == "/api/shutdown":
            MarkdownPreviewHandler.request_shutdown(delay=0.1)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"shutting_down"}')
            return

        if path == "/api/files":
            valid_exts = self.allowed_extensions if self.allowed_extensions is not None else DEFAULT_EXTENSIONS
            files = []
            for root, _, filenames in os.walk(self.target_dir):
                # Ignore hidden directories like .git, node_modules, .venv, etc.
                parts = Path(root).parts
                if any(p.startswith(".") or p in ("node_modules", "dist", "build", "__pycache__", ".venv", "venv", ".gradle") for p in parts):
                    continue

                for fn in filenames:
                    p = Path(fn)
                    ext = p.suffix.lower()
                    if ext in valid_exts:
                        full_p = Path(root) / fn
                        try:
                            rel = full_p.relative_to(self.target_dir).as_posix()
                            size = full_p.stat().st_size
                            files.append({
                                "name": fn,
                                "path": rel,
                                "size": size,
                                "ext": ext.lstrip(".")
                            })
                        except Exception:
                            continue

            files.sort(key=lambda x: x["path"].lower())
            resp = json.dumps({
                "root": str(self.target_dir.name or self.target_dir),
                "files": files,
                "default_expand": self.default_expand
            })

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(resp.encode("utf-8"))
            return

        if path == "/api/content":
            query = urllib.parse.parse_qs(parsed.query)
            rel_file = query.get("file", [""])[0]

            if not rel_file:
                self.send_error(400, "Missing 'file' parameter")
                return

            try:
                # Prevent directory traversal
                safe_path = (self.target_dir / rel_file).resolve()
                if not str(safe_path).startswith(str(self.target_dir.resolve())):
                    self.send_error(403, "Access denied")
                    return

                if not safe_path.is_file():
                    self.send_error(404, "File not found")
                    return

                content = safe_path.read_text(encoding="utf-8", errors="replace")
                ext = safe_path.suffix.lower()
                content_type = "text/plain; charset=utf-8"
                if ext in (".md", ".markdown"):
                    content_type = "text/markdown; charset=utf-8"
                elif ext == ".sql":
                    content_type = "text/x-sql; charset=utf-8"
                elif ext == ".json":
                    content_type = "application/json; charset=utf-8"
                elif ext == ".py":
                    content_type = "text/x-python; charset=utf-8"
                elif ext in (".ps1", ".psm1", ".psd1"):
                    content_type = "text/plain; charset=utf-8"
                elif ext in (".html", ".htm"):
                    content_type = "text/html; charset=utf-8"

                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(content.encode("utf-8"))
                return
            except Exception as e:
                self.send_error(500, f"Error reading file: {e}")
                return

        # Direct /raw/<path> route for raw file serving and rendered HTML/assets
        if path.startswith("/raw/"):
            rel_file = urllib.parse.unquote(path[5:])
            try:
                safe_path = (self.target_dir / rel_file).resolve()
                if not str(safe_path).startswith(str(self.target_dir.resolve())):
                    self.send_error(403, "Access denied")
                    return

                if not safe_path.is_file():
                    self.send_error(404, "File not found")
                    return

                mime_type, _ = mimetypes.guess_type(str(safe_path))
                if safe_path.suffix.lower() in (".html", ".htm"):
                    mime_type = "text/html; charset=utf-8"
                mime_type = mime_type or "application/octet-stream"

                self.send_response(200)
                self.send_header("Content-Type", mime_type)
                self.send_header("Content-Length", str(safe_path.stat().st_size))
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()

                with open(safe_path, "rb") as f:
                    while chunk := f.read(65536):
                        self.wfile.write(chunk)
                return
            except Exception as e:
                self.send_error(500, f"Error serving raw file: {e}")
                return

        if path == "/api/raw":
            query = urllib.parse.parse_qs(parsed.query)
            rel_file = query.get("file", [""])[0]

            if not rel_file:
                self.send_error(400, "Missing 'file' parameter")
                return

            try:
                safe_path = (self.target_dir / rel_file).resolve()
                if not str(safe_path).startswith(str(self.target_dir.resolve())):
                    self.send_error(403, "Access denied")
                    return

                if not safe_path.is_file():
                    self.send_error(404, "File not found")
                    return

                mime_type, _ = mimetypes.guess_type(str(safe_path))
                mime_type = mime_type or "application/octet-stream"

                self.send_response(200)
                self.send_header("Content-Type", mime_type)
                self.send_header("Content-Length", str(safe_path.stat().st_size))
                self.send_header("Cache-Control", "public, max-age=3600")
                self.end_headers()

                with open(safe_path, "rb") as f:
                    while chunk := f.read(65536):
                        self.wfile.write(chunk)
                return
            except Exception as e:
                self.send_error(500, f"Error serving file: {e}")
                return

        # Direct static file fallback (e.g. /client/public/img/look.png or /package.json)
        try:
            unquoted = urllib.parse.unquote(path.lstrip("/"))
            if unquoted and not unquoted.startswith("api/"):
                safe_path = (self.target_dir / unquoted).resolve()
                if str(safe_path).startswith(str(self.target_dir.resolve())) and safe_path.is_file():
                    mime_type, _ = mimetypes.guess_type(str(safe_path))
                    mime_type = mime_type or "application/octet-stream"

                    self.send_response(200)
                    self.send_header("Content-Type", mime_type)
                    self.send_header("Content-Length", str(safe_path.stat().st_size))
                    self.send_header("Cache-Control", "public, max-age=3600")
                    self.end_headers()

                    with open(safe_path, "rb") as f:
                        while chunk := f.read(65536):
                            self.wfile.write(chunk)
                    return
        except Exception:
            pass

        self.send_error(404, "Not Found")

    def log_message(self, format, *args):
        # Keep console output clean
        pass


def start_watchdog(server, timeout=6.0):
    """Watches browser connection and initiates shutdown if browser disconnects."""
    def watchdog_loop():
        start_time = time.time()
        while True:
            time.sleep(1.0)
            if MarkdownPreviewHandler.keep_alive:
                break
            if MarkdownPreviewHandler.has_connected:
                # Browser connected previously; verify heartbeat is active
                if (time.time() - MarkdownPreviewHandler.last_heartbeat) > timeout:
                    print("\nBrowser closed. Shutting down mdp. Goodbye!")
                    server.shutdown()
                    break
            else:
                # If no browser connects within 45s, terminate to avoid orphaned process
                if (time.time() - start_time) > 45.0:
                    print("\nNo browser connection detected within 45s. Shutting down mdp.")
                    server.shutdown()
                    break

    t = threading.Thread(target=watchdog_loop, daemon=True)
    t.start()
