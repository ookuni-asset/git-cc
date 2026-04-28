"""Conventional Commits validation."""
from __future__ import annotations

import re

CONVENTIONAL_RE = re.compile(
    r"^(?P<type>feat|fix|docs|refactor|test|chore|build|ci|perf|style)"
    r"(?:\((?P<scope>[a-z0-9._/-]+)\))?"
    r"(?P<breaking>!)?: "
    r"(?P<subject>.+?)"
    r"(?:\s+(?P<issue>#\d+))?$"
)


def validate(message: str) -> tuple[bool, str]:
    lines = [ln.rstrip("\n") for ln in message.splitlines()]
    if not lines or not lines[0].strip():
        return False, "1行目（タイトル）が空です"
    title = lines[0].strip()
    m = CONVENTIONAL_RE.match(title)
    if not m:
        return False, "1行目が Conventional Commits 形式ではありません (例: feat(api): 〜)"
    subject = m.group("subject")
    if subject.endswith(("。", ".")):
        return False, "subject の末尾に句点を含めないでください"
    return True, "ok"
