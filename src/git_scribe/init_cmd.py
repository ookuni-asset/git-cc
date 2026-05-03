"""`git scribe init` — bootstrap config/templates in a project."""
from __future__ import annotations

import sys
from pathlib import Path

from . import git


def run(*, cursor: bool, force: bool) -> int:
    root = git.try_repo_root()
    if root is None:
        print("ERROR: not inside a git repository", file=sys.stderr)
        return 2

    templates = Path(__file__).parent / "templates"
    targets: list[tuple[Path, Path]] = [
        (templates / "default-config.toml", root / ".gitscribe.toml"),
        (templates / "default-rules.md", root / "COMMIT_GUIDELINES.md"),
    ]
    if cursor:
        cursor_root = templates / "cursor"
        for src in cursor_root.rglob("*"):
            if src.is_file():
                rel = src.relative_to(cursor_root)
                targets.append((src, root / rel))

    written = 0
    skipped = 0
    for src, dst in targets:
        if dst.exists() and not force:
            print(f"skip (exists): {dst.relative_to(root)}")
            skipped += 1
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"wrote:         {dst.relative_to(root)}")
        written += 1

    print(f"\ndone. wrote {written}, skipped {skipped}.")
    if skipped and not force:
        print("(use --force to overwrite existing files)")
    return 0
