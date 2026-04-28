"""Build LLM prompts and resolve project rules."""
from __future__ import annotations

from pathlib import Path

from .changes import Changes
from .config import Config


def build(*, rules_text: str, changes: Changes, issue: str | None, patch: str) -> str:
    issue_hint = issue or ""
    files = "\n".join(f"- {f}" for f in changes.files)
    staged = "staged" if changes.staged else "mixed/unstaged"
    return "\n".join([
        "You are generating a git commit message for this repository.",
        "Follow the project's commit message rules EXACTLY.",
        "",
        "## Rules (authoritative)",
        rules_text.strip(),
        "",
        "## Inputs",
        f"- diff_source: {staged}",
        f"- issue: {issue_hint}",
        "",
        "### Changed files",
        files,
        "",
        "### diff --stat",
        changes.diff_stat.strip(),
        "",
        "### diff (patch)",
        patch.strip(),
        "",
        "## Output requirements",
        "- Output ONLY the final commit message as plain text.",
        "- Do NOT wrap in markdown fences.",
        "- First line must match Conventional Commits format from the rules.",
        "- Subject must not end with a Japanese period '。' or '.'",
        "- Body should focus on Why. Use '- ' bullets when body is present.",
    ]).strip() + "\n"


def resolve_rules_text(repo_root: Path, cfg: Config) -> str:
    for rel in cfg.rules_search:
        path = repo_root / rel
        if path.exists():
            return path.read_text(encoding="utf-8")
    bundled = Path(__file__).parent / "templates" / "default-rules.md"
    return bundled.read_text(encoding="utf-8")
