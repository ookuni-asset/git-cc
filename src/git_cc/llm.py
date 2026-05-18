"""External LLM CLI invocation."""
from __future__ import annotations

import shlex
import subprocess


def run(*, command: str, prompt: str, timeout_sec: int) -> str:
    """
    Invoke `command` as an external CLI.

    - If `command` contains '{prompt}', it is substituted (verbatim) and the
      resulting string is split with shlex and executed.
    - Otherwise the command is executed and `prompt` is sent on stdin.
    """
    cmd_str = command
    stdin_data: str | None
    if "{prompt}" in cmd_str:
        cmd_str = cmd_str.replace("{prompt}", prompt)
        stdin_data = None
    else:
        stdin_data = prompt
    cmd = shlex.split(cmd_str)
    if not cmd:
        raise RuntimeError("LLM command is empty")
    proc = subprocess.run(
        cmd,
        input=stdin_data,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout_sec,
    )
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        raise RuntimeError(f"LLM command failed (exit={proc.returncode}): {stderr}")
    return (proc.stdout or "").strip()


def strip_code_fences(s: str) -> str:
    t = s.strip()
    if not t.startswith("```"):
        return t
    lines = t.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    while lines and lines[-1].strip() == "":
        lines.pop()
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()
