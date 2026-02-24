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
