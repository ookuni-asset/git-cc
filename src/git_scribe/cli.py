"""CLI entry point for `git-scribe` / `git scribe`."""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path

from . import __version__
from . import changes as changes_mod
from . import config as config_mod
from . import editor as editor_mod
from . import git
from . import heuristics
from . import init_cmd
from . import llm
from . import prompt as prompt_mod
from . import validator

_SUBCOMMANDS = {"commit", "print", "init", "config", "doctor"}
_GLOBAL_FLAGS = {"--version", "-h", "--help"}


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    # Default to "commit" when no subcommand and no global flag is given.
    if not argv or (argv[0] not in _SUBCOMMANDS and argv[0] not in _GLOBAL_FLAGS):
        argv = ["commit", *argv]

    parser = argparse.ArgumentParser(
        prog="git-scribe",
        description="AI-assisted Conventional Commits CLI.",
    )
    parser.add_argument("--version", action="version", version=f"git-scribe {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_commit = sub.add_parser("commit", help="generate, edit, commit, push (default)")
    _add_main_args(p_commit)

    p_print = sub.add_parser("print", help="generate and print the message only")
    _add_main_args(p_print)

    p_init = sub.add_parser("init", help="bootstrap .gitscribe.toml and rule templates")
    p_init.add_argument("--cursor", action="store_true", help="also install Cursor rule and skill files")
    p_init.add_argument("--force", action="store_true", help="overwrite existing files")

    sub.add_parser("config", help="print resolved configuration")
    sub.add_parser("doctor", help="check environment readiness")

    args = parser.parse_args(argv)

    if args.cmd == "commit":
        return _run_main(args, print_only=False)
    if args.cmd == "print":
        return _run_main(args, print_only=True)
    if args.cmd == "init":
        return init_cmd.run(cursor=args.cursor, force=args.force)
    if args.cmd == "config":
        return _run_config()
    if args.cmd == "doctor":
        return _run_doctor()
    parser.print_help()
    return 2


def _add_main_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("-a", "--stage-all", action="store_true", help="run `git add -A` first")
    p.add_argument("--prefer-staged", action="store_true", help="generate from staged diff when available")
    p.add_argument("--issue", help="issue number (e.g. 123 or #123)")
    p.add_argument("--no-push", action="store_true", help="commit only, do not push")
    p.add_argument("--no-llm", action="store_true", help="skip LLM, use heuristic generator")
    p.add_argument("--llm-required", action="store_true", help="exit on LLM failure (no fallback)")
    p.add_argument("--llm-command", help="override [llm].command")
    p.add_argument("--llm-timeout-sec", type=int, help="override [llm].timeout_sec")
    p.add_argument("--config", help="path to .gitscribe.toml (override discovery)")
    p.add_argument("--lang", choices=["ja", "en"], help="fallback subject language")
    p.add_argument("--dry-run", action="store_true", help="generate but do not commit/push")


def _run_main(args: argparse.Namespace, *, print_only: bool) -> int:
    if not git.have("git"):
        print("git not found", file=sys.stderr)
        return 2
    try:
        root = git.repo_root()
    except Exception:
        print("not inside a git repository", file=sys.stderr)
        return 2

    explicit = Path(args.config).resolve() if args.config else None
    cfg = config_mod.load(repo_root=root, explicit=explicit)
    if args.llm_command:
        cfg.llm_command = args.llm_command
    if args.llm_timeout_sec:
        cfg.llm_timeout_sec = args.llm_timeout_sec
    if args.llm_required:
        cfg.llm_required = True
    if args.lang:
        cfg.output_lang = args.lang

    issue = _normalize_issue(args.issue)
    if args.issue and issue is None:
        print("--issue must be a number or #N", file=sys.stderr)
        return 2

    if args.stage_all:
        git.stage_all()

    ch = changes_mod.collect(prefer_staged=args.prefer_staged)
    if not ch.files:
        print("no changes to commit", file=sys.stderr)
        return 0

    print("=== changed files ===")
    for f in ch.files:
        print(f"- {f}")
    if ch.diff_stat:
        print("\n=== diff --stat ===")
        print(ch.diff_stat)
    print()

    msg = _generate_message(ch, cfg, root=root, issue=issue, no_llm=args.no_llm)

    if print_only:
        print("=== generated commit message ===")
        print(msg.rstrip("\n"))
        return 0

    if args.dry_run:
        print("=== dry-run: final message would be ===")
        print(msg.rstrip("\n"))
        return 0

    edited = editor_mod.review(msg)
    ok, reason = validator.validate(edited)
    if not ok:
        print(f"commit message does not follow rules: {reason}", file=sys.stderr)
        return 2

    if cfg.commit_trailer:
        edited = edited.rstrip("\n") + "\n\n" + cfg.commit_trailer.strip() + "\n"

    final_path = _write_temp(edited)
    try:
        git.commit_with_file(final_path)
    finally:
        try:
            final_path.unlink(missing_ok=True)
        except Exception:
            pass

    if args.no_push or not cfg.push_enabled:
        return 0
    if cfg.require_gh:
        git.gh_warmup()
    git.push()
    return 0


def _generate_message(
    ch,
    cfg,
    *,
    root: Path,
    issue: str | None,
    no_llm: bool,
) -> str:
    if no_llm:
        return heuristics.generate(ch, cfg, issue=issue)
    try:
        rules_text = prompt_mod.resolve_rules_text(root, cfg)
        patch = changes_mod.get_patch(ch)
        prompt = prompt_mod.build(
            rules_text=rules_text,
            changes=ch,
            issue=issue,
            patch=patch,
            output_lang=cfg.output_lang,
        )
        out = llm.run(command=cfg.llm_command, prompt=prompt, timeout_sec=cfg.llm_timeout_sec)
        out = llm.strip_code_fences(out)
        if not out.strip():
            raise RuntimeError("LLM returned empty output")
        return out.strip() + "\n"
    except Exception as e:
        if cfg.llm_required:
            print(f"LLM generation failed: {e}", file=sys.stderr)
            sys.exit(2)
        print(f"LLM generation failed; falling back to heuristics: {e}", file=sys.stderr)
        return heuristics.generate(ch, cfg, issue=issue)


def _normalize_issue(raw: str | None) -> str | None:
    if not raw:
        return None
    s = str(raw).strip()
    s = s if s.startswith("#") else f"#{s}"
    if not re.fullmatch(r"#\d+", s):
        return None
    return s


def _write_temp(content: str) -> Path:
    with tempfile.NamedTemporaryFile(prefix="git-scribe-final-", suffix=".txt", mode="w+", delete=False) as f:
        path = Path(f.name)
        f.write(content)
        f.flush()
    return path


def _run_config() -> int:
    try:
        root = git.repo_root()
    except Exception:
        root = None
    cfg = config_mod.load(repo_root=root)
    print(json.dumps(asdict(cfg), indent=2, ensure_ascii=False))
    return 0


def _run_doctor() -> int:
    ok = True

    def check(label: str, cond: bool, hint: str = "") -> None:
        nonlocal ok
        mark = "OK" if cond else "NG"
        suffix = f"  ({hint})" if hint and not cond else ""
        print(f"[{mark}] {label}{suffix}")
        if not cond:
            ok = False

    check("git available", git.have("git"))
    in_repo = False
    root: Path | None = None
    try:
        root = git.repo_root()
        in_repo = True
    except Exception:
        pass
    check("inside git repository", in_repo)

    cfg = config_mod.load(repo_root=root)
    cmd_first = cfg.llm_command.split()[0] if cfg.llm_command else ""
    check(
        f"LLM command available: {cmd_first or '(empty)'}",
        bool(cmd_first) and git.have(cmd_first),
        hint="install the CLI or set GIT_SCRIBE_LLM_COMMAND",
    )

    return 0 if ok else 1
