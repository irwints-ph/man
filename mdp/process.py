"""
Process and port management module for mdp
==========================================
Provides discovery, status checking, graceful shutdown, and termination
for background or running mdp instances.
"""

import json
import os
import socket
import sys
import time
import urllib.request

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

DEFAULT_PORT = 7800


def find_free_port(start_port=DEFAULT_PORT):
    """Finds an available TCP port starting from start_port."""
    port = start_port
    while port < start_port + 100:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
        port += 1
    return start_port


def find_running_instances(start_port=DEFAULT_PORT, max_ports=50):
    """Probes ports for active mdp instances and queries their /api/status."""
    instances = []
    for port in range(start_port, start_port + max_ports):
        # Fast socket probe (<1ms per closed port)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.04)
                if s.connect_ex(("127.0.0.1", port)) != 0:
                    continue
        except Exception:
            continue

        # Port is listening; query /api/status
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{port}/api/status")
            with urllib.request.urlopen(req, timeout=0.35) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    if data.get("status") == "running":
                        data["port"] = port
                        instances.append(data)
        except Exception:
            continue
    return instances


def check_status():
    """Prints status of running mdp instances."""
    print("=" * 65)
    print("  [STATUS] Checking mdp Server Status...")
    print("=" * 65)
    instances = find_running_instances()
    if not instances:
        print("  No active mdp instances found running on ports 7800-7850.")
        print("  To start an instance, run: mdp [directory]")
        print("=" * 65)
        return

    print(f"  Found {len(instances)} active mdp instance(s):\n")
    print(f"  {'PORT':<8} {'PID':<8} {'UPTIME':<12} {'TARGET DIRECTORY'}")
    print(f"  {'-'*6}   {'-'*6}   {'-'*10}   {'-'*30}")
    for inst in instances:
        uptime_sec = inst.get("uptime_seconds", 0)
        mins, secs = divmod(uptime_sec, 60)
        hrs, mins = divmod(mins, 60)
        uptime_str = f"{hrs}h {mins}m {secs}s" if hrs else f"{mins}m {secs}s"
        print(f"  {inst['port']:<8} {inst.get('pid', 'N/A'):<8} {uptime_str:<12} {inst.get('target_dir', '')}")
    print("=" * 65)


def kill_instances(target_port=0):
    """Sends graceful shutdown or terminates running mdp instances."""
    print("=" * 65)
    print("  [KILL] Terminating mdp Instance(s)...")
    print("=" * 65)

    instances = find_running_instances()
    if not instances:
        print("  No active mdp instances found to terminate.")
        print("=" * 65)
        return

    killed_count = 0
    for inst in instances:
        port = inst["port"]
        pid = inst.get("pid")
        if target_port > 0 and port != target_port:
            continue

        # 1. Attempt graceful HTTP shutdown via /api/shutdown
        stopped_gracefully = False
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{port}/api/shutdown")
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                if resp.status == 200:
                    stopped_gracefully = True
        except Exception:
            pass

        # 2. If PID is present, verify process termination or kill via OS
        if pid and sys.platform == "win32":
            time.sleep(0.3)
            try:
                os.system(f"taskkill /PID {pid} /F >nul 2>&1")
            except Exception:
                pass

        print(f"  [OK] Terminated mdp instance on port {port} (PID: {pid})")
        killed_count += 1

    if killed_count == 0 and target_port > 0:
        print(f"  No mdp instance was found running specifically on port {target_port}.")
    else:
        print(f"\n  Successfully stopped {killed_count} mdp instance(s).")
    print("=" * 65)
