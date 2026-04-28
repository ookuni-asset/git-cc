"""Thin git invocation helpers."""
from __future__ import annotations

import subprocess
from pathlib import Path
from shutil import which


def have(cmd: str) -> bool:
    return which(cmd) is not None


def run(args: list[str], *, check: bool = True, capture: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], check=check, text=True, capture_output=capture)


def output(args: list[str]) -> str:
    return run(args).stdout.strip()


def repo_root() -> Path:
    return Path(output(["rev-parse", "--show-toplevel"]))


def stage_all() -> None:
    subprocess.run(["git", "add", "-A"], check=True)


def commit_with_file(path: Path) -> None:
    subprocess.run(["git", "commit", "-F", str(path)], check=True)


def push() -> None:
    upstream = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
        capture_output=True,
        text=True,
    )
    if upstream.returncode != 0:
        branch = output(["rev-parse", "--abbrev-ref", "HEAD"])
        subprocess.run(["git", "push", "-u", "origin", branch], check=True)
    else:
        subprocess.run(["git", "push"], check=True)


def gh_warmup() -> None:
    """Best-effort gh repo bookkeeping. Failures are silent."""
    for args in (["gh", "repo", "set-default"], ["gh", "auth", "status"], ["gh", "repo", "sync"]):
        subprocess.run(args, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
