"""
Shell and system execution tools for APEX AI Agent.

Enables the agent to autonomously run shell commands, manage files,
run build pipelines, and handle multi-step devops tasks.

Security notes:
  - Commands run in a subprocess with a configurable working directory.
  - There is NO sandboxing by design — the agent needs full system access
    to autonomously build and deploy real applications.
  - Only expose this agent to trusted users.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

from utils.logger import log

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

_DEFAULT_WORK_DIR = str(Path.home() / "apex_workspace")
_MAX_OUTPUT_CHARS = 8000   # truncate long outputs before sending to model


def _ensure_workdir(path: str) -> Path:
    """Create the working directory if it doesn't exist."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _truncate(text: str, max_chars: int = _MAX_OUTPUT_CHARS) -> str:
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return text[:half] + f"\n\n... [{len(text) - max_chars} chars truncated] ...\n\n" + text[-half:]


# ─────────────────────────────────────────────
# RUN SHELL COMMAND
# ─────────────────────────────────────────────

def run_command(
    command: str,
    working_directory: Optional[str] = None,
    timeout_seconds: int = 120,
    env_overrides: Optional[dict] = None,
    shell: bool = True,
) -> dict:
    """
    Execute a shell command and return the output.

    Supports any command: git, npm, pip, python, node, curl, mkdir, touch, etc.

    Args:
        command: Shell command to run (e.g. 'npm install', 'git init', 'python app.py').
        working_directory: Directory to run in (created automatically if missing).
        timeout_seconds: Max execution time (default 120).
        env_overrides: Extra environment variables to inject.
        shell: Use shell=True (allows pipes, &&, etc. on the target OS).

    Returns:
        Dict with: success, stdout, stderr, return_code, command, working_directory.
    """
    work_dir = working_directory or _DEFAULT_WORK_DIR
    work_path = Path(work_dir)
    work_path.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)

    log.info(f"run_command: [{work_dir}] $ {command[:120]}")

    start = time.time()
    try:
        result = subprocess.run(
            command,
            shell=shell,
            cwd=str(work_path),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        elapsed = round(time.time() - start, 2)
        stdout = _truncate(result.stdout.strip())
        stderr = _truncate(result.stderr.strip())
        success = result.returncode == 0

        if success:
            log.success(f"Command succeeded in {elapsed}s: {command[:60]}")
        else:
            log.warning(f"Command failed (rc={result.returncode}): {command[:60]}\n{stderr[:200]}")

        return {
            "success": success,
            "stdout": stdout,
            "stderr": stderr,
            "return_code": result.returncode,
            "elapsed_seconds": elapsed,
            "command": command,
            "working_directory": str(work_path),
        }

    except subprocess.TimeoutExpired:
        log.error(f"Command timed out after {timeout_seconds}s: {command[:80]}")
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Timed out after {timeout_seconds} seconds",
            "return_code": -1,
            "elapsed_seconds": timeout_seconds,
            "command": command,
            "working_directory": str(work_path),
        }
    except Exception as exc:
        log.error(f"run_command exception: {exc}")
        return {
            "success": False,
            "stdout": "",
            "stderr": str(exc),
            "return_code": -1,
            "elapsed_seconds": 0,
            "command": command,
            "working_directory": str(work_path),
        }


# ─────────────────────────────────────────────
# WRITE FILE TO DISK
# ─────────────────────────────────────────────

def write_file(
    file_path: str,
    content: str,
    working_directory: Optional[str] = None,
) -> dict:
    """
    Write text content to a file, creating parent directories as needed.

    Args:
        file_path: File path (relative to working_directory, or absolute).
        content: Text content to write.
        working_directory: Base directory (default: ~/apex_workspace).

    Returns:
        Dict with: success, absolute_path, size_bytes.
    """
    base = Path(working_directory or _DEFAULT_WORK_DIR)
    base.mkdir(parents=True, exist_ok=True)

    absolute = (base / file_path) if not Path(file_path).is_absolute() else Path(file_path)
    absolute.parent.mkdir(parents=True, exist_ok=True)

    try:
        absolute.write_text(content, encoding="utf-8")
        log.success(f"Wrote {absolute.stat().st_size} bytes to {absolute}")
        return {
            "success": True,
            "absolute_path": str(absolute),
            "size_bytes": absolute.stat().st_size,
        }
    except Exception as exc:
        log.error(f"write_file failed: {exc}")
        return {"success": False, "absolute_path": str(absolute), "error": str(exc)}


# ─────────────────────────────────────────────
# READ FILE FROM DISK
# ─────────────────────────────────────────────

def read_file(file_path: str, working_directory: Optional[str] = None) -> str:
    """
    Read text content from a file.

    Args:
        file_path: File path (relative or absolute).
        working_directory: Base directory.

    Returns:
        File content as a string, or an error message.
    """
    base = Path(working_directory or _DEFAULT_WORK_DIR)
    absolute = (base / file_path) if not Path(file_path).is_absolute() else Path(file_path)

    try:
        content = absolute.read_text(encoding="utf-8", errors="replace")
        log.info(f"Read {len(content)} chars from {absolute}")
        return content
    except FileNotFoundError:
        return f"[File not found: {absolute}]"
    except Exception as exc:
        return f"[Read error: {exc}]"


# ─────────────────────────────────────────────
# LIST DIRECTORY
# ─────────────────────────────────────────────

def list_directory(
    path: str = ".",
    working_directory: Optional[str] = None,
    max_items: int = 100,
) -> str:
    """
    List the contents of a directory.

    Args:
        path: Directory path (relative or absolute).
        working_directory: Base directory.
        max_items: Max entries to return.

    Returns:
        Formatted directory listing.
    """
    base = Path(working_directory or _DEFAULT_WORK_DIR)
    target = (base / path) if not Path(path).is_absolute() else Path(path)

    if not target.exists():
        return f"Directory not found: {target}"

    try:
        entries = sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name))
        lines = [f"## Directory: {target}\n"]
        for i, entry in enumerate(entries[:max_items]):
            icon = "📁" if entry.is_dir() else "📄"
            size = f"  ({entry.stat().st_size:,} bytes)" if entry.is_file() else ""
            lines.append(f"{icon} {entry.name}{size}")
        if len(entries) > max_items:
            lines.append(f"… and {len(entries) - max_items} more items")
        return "\n".join(lines)
    except Exception as exc:
        return f"[list_directory error: {exc}]"


# ─────────────────────────────────────────────
# SYSTEM INFO
# ─────────────────────────────────────────────

def system_info() -> dict:
    """
    Return information about the running environment.
    Useful for the agent to decide which commands to use.
    """
    info = {
        "os": platform.system(),
        "os_version": platform.version(),
        "python_version": sys.version.split()[0],
        "working_directory": _DEFAULT_WORK_DIR,
        "tools_available": {},
    }

    # Probe common CLI tools
    for tool in ["git", "node", "npm", "npx", "python", "python3", "pip", "pip3",
                 "docker", "curl", "wget", "make", "gcc", "mvn", "java"]:
        info["tools_available"][tool] = shutil.which(tool) is not None

    return info


# ─────────────────────────────────────────────
# GIT HELPERS  (higher-level wrappers)
# ─────────────────────────────────────────────

def git_clone(repo_url: str, target_dir: Optional[str] = None) -> dict:
    """Clone a git repository."""
    base = _DEFAULT_WORK_DIR
    if target_dir is None:
        repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
        target_dir = str(Path(base) / repo_name)
    return run_command(f"git clone {repo_url} {target_dir}", working_directory=base)


def git_init_and_push(
    local_dir: str,
    remote_url: str,
    commit_message: str = "initial commit",
    branch: str = "main",
) -> dict:
    """
    Initialize a git repo in a local directory and push it to a remote URL.

    Returns combined result of all git commands.
    """
    commands = [
        f"git init",
        f"git checkout -b {branch}",
        f"git add .",
        f'git commit -m "{commit_message}"',
        f"git remote add origin {remote_url}",
        f"git push -u origin {branch}",
    ]
    results = []
    for cmd in commands:
        r = run_command(cmd, working_directory=local_dir)
        results.append({"cmd": cmd, **r})
        if not r["success"] and "already exists" not in r["stderr"]:
            break  # stop on failure (except harmless "already exists")

    final_success = all(
        r["success"] or "already exists" in r.get("stderr", "") or "nothing to commit" in r.get("stdout", "")
        for r in results
    )
    return {
        "success": final_success,
        "steps": results,
        "local_dir": local_dir,
        "remote": remote_url,
    }


# ─────────────────────────────────────────────
# DEVICE DETAILS  (CPU, RAM, disk, network, battery, OS)
# ─────────────────────────────────────────────

def get_device_details() -> dict:
    """
    Collect comprehensive hardware and OS information about the host device.

    Returns a dict with sections:
      - os: system, release, version, architecture, hostname, uptime
      - cpu: brand, physical_cores, logical_cores, frequency_mhz, usage_percent
      - memory: total_gb, available_gb, used_gb, percent
      - disks: list of {device, mountpoint, fs, total_gb, used_gb, free_gb, percent}
      - network_interfaces: list of {name, addresses}
      - battery: present, percent, plugged_in, hours_left  (None if no battery)
      - python: version, executable
      - tools_available: dict of {tool: bool}
    """
    import datetime

    info: dict = {}

    # ——— OS ———
    info["os"] = {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "architecture": platform.machine(),
        "hostname": platform.node(),
        "processor": platform.processor() or "unknown",
    }

    # ——— Try psutil for rich hardware data ———
    try:
        import psutil  # type: ignore

        # Uptime
        boot_ts = psutil.boot_time()
        uptime_secs = time.time() - boot_ts
        info["os"]["uptime"] = str(datetime.timedelta(seconds=int(uptime_secs)))
        info["os"]["boot_time"] = datetime.datetime.fromtimestamp(boot_ts).strftime("%Y-%m-%d %H:%M:%S")

        # CPU
        freq = psutil.cpu_freq()
        info["cpu"] = {
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "frequency_mhz": round(freq.current, 1) if freq else None,
            "max_frequency_mhz": round(freq.max, 1) if freq else None,
            "usage_percent": psutil.cpu_percent(interval=0.5),
            "per_core_usage": psutil.cpu_percent(interval=0.5, percpu=True),
        }

        # Memory
        vm = psutil.virtual_memory()
        info["memory"] = {
            "total_gb": round(vm.total / 1e9, 2),
            "available_gb": round(vm.available / 1e9, 2),
            "used_gb": round(vm.used / 1e9, 2),
            "percent": vm.percent,
        }
        swap = psutil.swap_memory()
        info["swap"] = {
            "total_gb": round(swap.total / 1e9, 2),
            "used_gb": round(swap.used / 1e9, 2),
            "percent": swap.percent,
        }

        # Disks
        disks = []
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append({
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "filesystem": part.fstype,
                    "total_gb": round(usage.total / 1e9, 2),
                    "used_gb": round(usage.used / 1e9, 2),
                    "free_gb": round(usage.free / 1e9, 2),
                    "percent": usage.percent,
                })
            except PermissionError:
                pass
        info["disks"] = disks

        # Network interfaces
        ifaces = []
        for name, addrs in psutil.net_if_addrs().items():
            addr_list = []
            for addr in addrs:
                entry = {"family": str(addr.family).split(".")[-1], "address": addr.address}
                if addr.netmask:
                    entry["netmask"] = addr.netmask
                addr_list.append(entry)
            ifaces.append({"interface": name, "addresses": addr_list})
        info["network_interfaces"] = ifaces

        # Network I/O stats
        net_io = psutil.net_io_counters()
        info["network_io"] = {
            "bytes_sent_mb": round(net_io.bytes_sent / 1e6, 2),
            "bytes_recv_mb": round(net_io.bytes_recv / 1e6, 2),
        }

        # Battery
        battery = psutil.sensors_battery()
        if battery:
            hours_left = None
            if battery.secsleft not in (-1, -2) and battery.secsleft > 0:
                hours_left = round(battery.secsleft / 3600, 2)
            info["battery"] = {
                "present": True,
                "percent": round(battery.percent, 1),
                "plugged_in": battery.power_plugged,
                "hours_left": hours_left,
            }
        else:
            info["battery"] = {"present": False}

        # Top 10 processes by CPU
        procs = []
        for p in sorted(
            psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]),
            key=lambda x: x.info.get("cpu_percent") or 0,
            reverse=True,
        )[:10]:
            procs.append(p.info)
        info["top_processes"] = procs

    except ImportError:
        info["psutil_note"] = "psutil not installed — limited hardware info available"
    except Exception as exc:
        info["psutil_error"] = str(exc)

    # Python runtime
    info["python"] = {
        "version": sys.version.split()[0],
        "executable": sys.executable,
    }

    # Available CLI tools
    info["tools_available"] = {
        t: shutil.which(t) is not None
        for t in ["git", "node", "npm", "python", "python3", "pip",
                  "docker", "curl", "wget", "make", "java", "mvn",
                  "ffmpeg", "code", "wsl", "ssh", "netsh"]
    }

    log.success("get_device_details: collected device info")
    return info


# ─────────────────────────────────────────────
# WIFI PASSWORDS
# ─────────────────────────────────────────────

def get_wifi_passwords() -> str:
    """
    Retrieve saved Wi-Fi network names and their passwords from the OS.

    Supports Windows, macOS, and Linux (NetworkManager).

    Returns:
        Formatted string listing every saved SSID and its password.
    """
    os_name = platform.system()
    log.info(f"get_wifi_passwords: platform={os_name}")

    try:
        if os_name == "Windows":
            return _wifi_windows()
        elif os_name == "Darwin":
            return _wifi_macos()
        elif os_name == "Linux":
            return _wifi_linux()
        else:
            return f"⚠️ Unsupported platform for Wi-Fi password retrieval: {os_name}"
    except Exception as exc:
        log.error(f"get_wifi_passwords error: {exc}")
        return f"❌ Error retrieving Wi-Fi passwords: {exc}"


def _wifi_windows() -> str:
    """
    Enumerate Wi-Fi profiles on Windows using `netsh` and extract passwords.
    Requires the process to run with sufficient privileges.
    """
    # List all saved profiles
    try:
        profiles_out = subprocess.check_output(
            ["netsh", "wlan", "show", "profiles"],
            text=True, stderr=subprocess.STDOUT, timeout=15,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return f"❌ Could not list Wi-Fi profiles: {exc}"

    ssids = []
    for line in profiles_out.splitlines():
        # Line format (EN): '    All User Profile     : MyNetwork'
        if ":" in line and ("Profile" in line or "All User" in line or "User Profile" in line):
            parts = line.split(":", 1)
            if len(parts) == 2:
                ssid = parts[1].strip()
                if ssid:
                    ssids.append(ssid)

    if not ssids:
        return "⚠️ No saved Wi-Fi profiles found on this device."

    results = [f"## Saved Wi-Fi Networks & Passwords ({len(ssids)} profiles)\n"]
    for ssid in ssids:
        try:
            detail = subprocess.check_output(
                ["netsh", "wlan", "show", "profile", f"name={ssid}", "key=clear"],
                text=True, stderr=subprocess.STDOUT, timeout=10,
            )
            password = None
            security_key_present = False
            for detail_line in detail.splitlines():
                # Password line (EN): 'Key Content            : mypassword'
                if "Key Content" in detail_line or "\u5bc6\u7801" in detail_line or "Schl\xfcsselinhalt" in detail_line:
                    pw_parts = detail_line.split(":", 1)
                    if len(pw_parts) == 2:
                        password = pw_parts[1].strip() or "(empty password)"
                    break
                # Detect if a key is saved but hidden (no admin)
                if "Security key" in detail_line and "Present" in detail_line:
                    security_key_present = True
            if password is None:
                password = (
                    "(saved — run app as Administrator to reveal password)"
                    if security_key_present
                    else "(open network / no password)"
                )
        except Exception:
            password = "(access denied — run as administrator)"
        results.append(f"**SSID:** {ssid}\n**Password:** {password}\n")

    return "\n".join(results)


def _wifi_macos() -> str:
    """
    Retrieve Wi-Fi passwords on macOS via the `security` keychain command.
    May prompt for user authorisation per SSID.
    """
    # Get preferred networks via airport CLI
    airport = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
    try:
        prefs_out = subprocess.check_output(
            [airport, "-I"], text=True, stderr=subprocess.STDOUT, timeout=10,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        prefs_out = ""

    # Also list from networksetup
    ssids = []
    try:
        hw_out = subprocess.check_output(
            ["networksetup", "-listpreferredwirelessnetworks", "en0"],
            text=True, stderr=subprocess.STDOUT, timeout=10,
        )
        for line in hw_out.splitlines()[1:]:
            s = line.strip()
            if s:
                ssids.append(s)
    except Exception:
        pass

    if not ssids:
        return "⚠️ No saved Wi-Fi profiles found (or permission denied on macOS)."

    results = [f"## Saved Wi-Fi Networks & Passwords ({len(ssids)} profiles)\n"]
    for ssid in ssids:
        try:
            pw = subprocess.check_output(
                ["security", "find-generic-password", "-D",
                 "AirPort network password", "-a", ssid, "-w"],
                text=True, stderr=subprocess.DEVNULL, timeout=10,
            ).strip()
            password = pw or "(empty password)"
        except subprocess.CalledProcessError:
            password = "(not saved in keychain)"
        except Exception as exc:
            password = f"(error: {exc})"
        results.append(f"**SSID:** {ssid}\n**Password:** {password}\n")

    return "\n".join(results)


def _wifi_linux() -> str:
    """
    Read Wi-Fi passwords from NetworkManager connection files on Linux.
    Requires read access to /etc/NetworkManager/system-connections/ (usually root).
    """
    nm_dir = Path("/etc/NetworkManager/system-connections")
    if not nm_dir.exists():
        # Try nmcli as fallback
        try:
            out = subprocess.check_output(
                ["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"],
                text=True, stderr=subprocess.STDOUT, timeout=10,
            )
            wifi_names = [
                line.split(":")[0]
                for line in out.splitlines()
                if "wireless" in line or "wifi" in line
            ]
        except Exception:
            return "⚠️ NetworkManager directory not found and nmcli unavailable."

        results = [f"## Saved Wi-Fi Networks ({len(wifi_names)} found)\n"]
        for name in wifi_names:
            try:
                pw_out = subprocess.check_output(
                    ["nmcli", "-s", "-g", "802-11-wireless-security.psk",
                     "connection", "show", name],
                    text=True, stderr=subprocess.STDOUT, timeout=10,
                ).strip()
                password = pw_out or "(empty password or not stored)"
            except Exception:
                password = "(access denied — run as root)"
            results.append(f"**SSID:** {name}\n**Password:** {password}\n")
        return "\n".join(results)

    # Read .nmconnection files directly
    import configparser
    files = list(nm_dir.glob("*"))
    if not files:
        return "⚠️ No connection files found in NetworkManager directory."

    results = []
    for conn_file in files:
        try:
            config = configparser.ConfigParser()
            config.read(str(conn_file))
            conn_type = config.get("connection", "type", fallback="")
            if "wireless" not in conn_type and "wifi" not in conn_type:
                continue
            ssid = config.get("wifi", "ssid", fallback=conn_file.name)
            password = config.get("wifi-security", "psk", fallback="(open network)").strip('"')
            results.append(f"**SSID:** {ssid}\n**Password:** {password}\n")
        except Exception:
            pass

    if not results:
        return "⚠️ No Wi-Fi profiles found (or access denied — run as root)."

    return f"## Saved Wi-Fi Networks & Passwords ({len(results)} profiles)\n\n" + "\n".join(results)
