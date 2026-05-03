"""Editor invocation for human review."""
from __future__ import annotations

import os
import shlex
import subprocess
import tempfile
from contextlib import suppress
from pathlib import Path


def review(initial: str) -> str:
    editor = os.getenv("GIT_EDITOR") or os.getenv("VISUAL") or os.getenv("EDITOR") or "vi"
    with tempfile.NamedTemporaryFile(prefix="git-scribe-", suffix=".txt", mode="w+", delete=False) as f:
        path = Path(f.name)
        f.write(initial)
        f.flush()
    try:
        cmd = shlex.split(editor) + [str(path)]
        subprocess.run(cmd, check=True)
        return path.read_text(encoding="utf-8")
    finally:
        with suppress(Exception):
            path.unlink(missing_ok=True)
