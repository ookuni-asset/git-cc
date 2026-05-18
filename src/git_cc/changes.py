"""Collect git changes for prompt building."""
from __future__ import annotations

from dataclasses import dataclass

from . import git


@dataclass(frozen=True)
class Changes:
    staged: bool
    files: list[str]
    diff_stat: str
    name_status: list[tuple[str, str]]


def collect() -> Changes:
    staged_files = git.output(["diff", "--cached", "--name-only"]).splitlines()
    diff_stat = git.output(["diff", "--cached", "--stat"])
    name_status = _parse_name_status(git.output(["diff", "--cached", "--name-status"]))
    return Changes(staged=True, files=staged_files, diff_stat=diff_stat, name_status=name_status)


def get_patch(changes: Changes) -> str:
    return git.output(["diff", "--cached", "--no-color"])


def _parse_name_status(text: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for ln in text.splitlines():
        parts = ln.split("\t", 1)
        if len(parts) == 2:
            out.append((parts[0], parts[1]))
    return out
