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


def try_repo_root() -> Path | None:
    result = run(["rev-parse", "--show-toplevel"], check=False)
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip())


def repo_root() -> Path:
    root = try_repo_root()
    if root is None:
        raise RuntimeError("not inside a git repository")
    return root


def stage_all() -> None:
    run(["add", "-A"], capture=False)


def commit_with_file(path: Path) -> None:
    run(["commit", "-F", str(path)], capture=False)


def push() -> None:
    upstream = run(
        ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
        check=False,
    )
    if upstream.returncode != 0:
        branch = output(["rev-parse", "--abbrev-ref", "HEAD"])
        run(["push", "-u", "origin", branch], capture=False)
    else:
        run(["push"], capture=False)


def gh_warmup() -> None:
    """Best-effort gh repo bookkeeping. Failures are silent."""
    for args in (["gh", "repo", "set-default"], ["gh", "auth", "status"], ["gh", "repo", "sync"]):
        subprocess.run(args, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
