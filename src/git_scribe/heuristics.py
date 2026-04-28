"""Local fallback message generation (config-driven, language-agnostic).

This is intentionally minimal — heavy lifting belongs in the LLM path. The
heuristic only ensures git-scribe can still produce a syntactically valid
commit message when the LLM is unavailable.
"""
from __future__ import annotations

import re

from .changes import Changes
from .config import Config

_FALLBACK_SUBJECT = {"ja": "変更を反映", "en": "Update"}


def guess_scope(files: list[str], cfg: Config) -> str | None:
    for m in cfg.scope_mappings:
        if any(f.startswith(m.prefix) for f in files):
            return m.scope
    return None


def guess_type(files: list[str], cfg: Config) -> str:
    if files and _all_match(files, cfg.type_docs_globs):
        return "docs"
    if _any_match(files, cfg.type_ci_globs):
        return "ci"
    if _any_match(files, cfg.type_build_globs):
        return "build"
    if _any_match(files, cfg.type_test_globs):
        return "test"
    return cfg.type_fallback


def fallback_subject(cfg: Config) -> str:
    return _FALLBACK_SUBJECT.get(cfg.fallback_lang, _FALLBACK_SUBJECT["en"])


def generate(changes: Changes, cfg: Config, *, issue: str | None) -> str:
    scope = guess_scope(changes.files, cfg)
    ctype = guess_type(changes.files, cfg)
    subject = fallback_subject(cfg)
    header = f"{ctype}{f'({scope})' if scope else ''}: {subject}"
    if issue:
        header += f" {issue}"
    return header + "\n"


def _any_match(files: list[str], globs: list[str]) -> bool:
    return any(match(f, g) for f in files for g in globs)


def _all_match(files: list[str], globs: list[str]) -> bool:
    return all(any(match(f, g) for g in globs) for f in files)


def match(path: str, glob: str) -> bool:
    """Glob match supporting `**` (any number of path components)."""
    return re.match(_glob_to_regex(glob), path) is not None


def _glob_to_regex(glob: str) -> str:
    out = ["^"]
    i = 0
    while i < len(glob):
        c = glob[i]
        if c == "*":
            if i + 1 < len(glob) and glob[i + 1] == "*":
                # `**/` -> zero or more path components, `**` -> anything
                if i + 2 < len(glob) and glob[i + 2] == "/":
                    out.append("(?:.*/)?")
                    i += 3
                else:
                    out.append(".*")
                    i += 2
            else:
                out.append("[^/]*")
                i += 1
        elif c == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(c))
            i += 1
    out.append("$")
    return "".join(out)
