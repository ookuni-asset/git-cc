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


def collect(*, prefer_staged: bool) -> Changes:
    staged_files = git.output(["diff", "--cached", "--name-only"]).splitlines()
    unstaged_files = git.output(["diff", "--name-only"]).splitlines()
    untracked_files = git.output(["ls-files", "--others", "--exclude-standard"]).splitlines()

    if prefer_staged and staged_files:
        diff_stat = git.output(["diff", "--cached", "--stat"])
        name_status = _parse_name_status(git.output(["diff", "--cached", "--name-status"]))
        return Changes(staged=True, files=staged_files, diff_stat=diff_stat, name_status=name_status)

    files = sorted(set(staged_files + unstaged_files + untracked_files))
    diff_stat = git.output(["diff", "--stat"])
    if untracked_files:
        extra = "\n".join(f" {f} | new file" for f in untracked_files)
        diff_stat = (diff_stat + "\n" + extra).strip()
    name_status = _parse_name_status(git.output(["diff", "--name-status"]))
    name_status += [("A", f) for f in untracked_files]
    return Changes(staged=False, files=files, diff_stat=diff_stat, name_status=name_status)


def get_patch(changes: Changes) -> str:
    if changes.staged:
        return git.output(["diff", "--cached", "--no-color"])
    return git.output(["diff", "--no-color"])


def _parse_name_status(text: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for ln in text.splitlines():
        parts = ln.split("\t", 1)
        if len(parts) == 2:
            out.append((parts[0], parts[1]))
    return out
