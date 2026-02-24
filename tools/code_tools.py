"""
Code execution and debugging tools.
Safely executes Python code in a subprocess sandbox.
"""
import os
import subprocess
import sys
import tempfile
import time
from typing import Any, Dict

from utils.logger import log


def execute_python_code(
    code: str,
    timeout_seconds: int = 30,
    capture_output: bool = True,
) -> Dict[str, Any]:
    """
    Safely execute Python code in a subprocess sandbox.

    Args:
        code: Python code string to execute
        timeout_seconds: Maximum execution time
        capture_output: Whether to capture stdout/stderr

    Returns:
        Dict with: success, stdout, stderr, return_code, execution_time_seconds
    """
    log.info("Executing Python code in sandbox...")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        temp_file = f.name

    try:
        start_time = time.time()
        result = subprocess.run(
            [sys.executable, temp_file],
            capture_output=capture_output,
            text=True,
            timeout=timeout_seconds,
        )
        execution_time = time.time() - start_time

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
            "execution_time_seconds": round(execution_time, 3),
        }

    except subprocess.TimeoutExpired:
        log.warning(f"Code execution timed out after {timeout_seconds}s")
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Execution timed out after {timeout_seconds} seconds",
            "return_code": -1,
            "execution_time_seconds": timeout_seconds,
        }

    except Exception as e:
        log.error(f"Code execution error: {e}")
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "return_code": -1,
            "execution_time_seconds": 0,
        }

    finally:
        try:
            os.unlink(temp_file)
        except OSError:
            pass


def analyze_code_for_bugs(code: str, language: str = "python") -> str:
    """
    Prepare code for Claude to analyze for bugs.
    Returns a structured prompt for the AI to use when reviewing code.

    Args:
        code: Source code to analyze
        language: Programming language

    Returns:
        Formatted analysis request string
    """
    return f"""
Perform a comprehensive code review and bug analysis for the following {language} code.

Identify and explain:
1. **Bugs** — Logic errors, runtime exceptions, edge cases
2. **Security Issues** — SQL injection, XSS, insecure inputs, etc.
3. **Performance Issues** — Inefficient loops, memory leaks, N+1 queries
4. **Code Quality** — Missing error handling, poor naming, code smells
5. **Best Practice Violations** — Language-specific standards

For each issue, provide:
- Line number (if applicable)
- Issue description
- Severity: Critical / High / Medium / Low
- Fixed code snippet

Code to analyze:
```{language}
{code}
```

After the analysis, provide the complete corrected version of the code.
"""
