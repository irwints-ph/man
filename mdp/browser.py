"""
Browser automation and launcher module for mdp
==============================================
Provides robust browser launching across Windows, macOS, and Linux
supporting default, Chrome, Edge, and Firefox.
"""

import os
import sys
import webbrowser


def open_browser(url: str, browser_name: str = "default"):
    """Robust browser launcher supporting specific browsers (chrome, msedge, edge, firefox, default)."""
    target = (browser_name or "default").lower().strip()

    if target in ("edge", "msedge", "e"):
        if sys.platform == "win32":
            try:
                os.system(f'start msedge "{url}"')
                return
            except Exception:
                pass
        try:
            b = webbrowser.get("msedge")
            b.open(url)
            return
        except Exception:
            pass

    elif target in ("chrome", "c", "gc"):
        if sys.platform == "win32":
            chrome_candidates = [
                os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Google\Chrome\Application\chrome.exe"),
                os.path.join(os.environ.get("PROGRAMFILES", ""), r"Google\Chrome\Application\chrome.exe"),
                os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), r"Google\Chrome\Application\chrome.exe"),
            ]
            for candidate in chrome_candidates:
                if os.path.isfile(candidate):
                    try:
                        os.system(f'start "" "{candidate}" "{url}"')
                        return
                    except Exception:
                        pass
            try:
                os.system(f'start chrome "{url}"')
                return
            except Exception:
                pass
        try:
            b = webbrowser.get("google-chrome") or webbrowser.get("chrome")
            b.open(url)
            return
        except Exception:
            pass
    elif target in ("brave", "b"):
        if sys.platform == "win32":
            try:
                os.system(f'start brave "{url}"')
                return
            except Exception:
                pass

    elif target in ("firefox", "f"):
        if sys.platform == "win32":
            try:
                os.system(f'start firefox "{url}"')
                return
            except Exception:
                pass
        try:
            b = webbrowser.get("firefox")
            b.open(url)
            return
        except Exception:
            pass

    # Default browser handling
    try:
        if not webbrowser.open(url):
            if sys.platform == "win32":
                os.system(f'start "" "{url}"')
    except Exception:
        if sys.platform == "win32":
            try:
                os.system(f'start "" "{url}"')
            except Exception:
                pass
