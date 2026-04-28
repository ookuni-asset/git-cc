# git-scribe

AI-assisted Conventional Commits CLI. Generate a commit message from your diff, review it in `$EDITOR`, then commit and push — in one command.

Designed to be **language-agnostic**: works for Python, PHP, TypeScript, Go, Rust, etc. All project-specific rules live in `.gitscribe.toml`, not in the tool's source code.

## Install (local / private)

This repository is currently private. Install from a local checkout:

```bash
# uv (recommended for local dev)
uv tool install --from /path/to/git-scribe git-scribe

# or pipx, from local path
pipx install /path/to/git-scribe
```

After install, both `git-scribe` and `git scribe` work — Git auto-discovers `git-*` binaries on `PATH`.

## Quick start

```bash
cd your-project
git scribe init                  # creates .gitscribe.toml and COMMIT_GUIDELINES.md
git add -A
git scribe                       # generate → review in $EDITOR → commit → push
```

## Common usage

```bash
git scribe -a                    # stage everything, then run main flow
git scribe --issue 123           # append #123 to the subject
git scribe --no-push             # commit only
git scribe print                 # generate and print, no commit
git scribe --no-llm              # skip LLM, use heuristic fallback
git scribe --dry-run             # show the message without committing
git scribe doctor                # check git/LLM/config readiness
```

`git scribe` (no subcommand) defaults to the main flow.

## LLM backend

By default `git-scribe` shells out to `claude`. Override per project or globally:

```toml
# .gitscribe.toml
[llm]
command     = "codex exec {prompt}"   # or "llm -m gpt-4o", "claude -p {prompt}", etc.
timeout_sec = 60
required    = false                   # if true, fail when LLM fails (no fallback)
```

```bash
GIT_SCRIBE_LLM_COMMAND="llm -m gpt-4o" git scribe
GIT_SCRIBE_LLM_TIMEOUT_SEC=120        git scribe
```

When the command string contains `{prompt}` it is substituted; otherwise the prompt is sent on stdin.

## Configuration

`.gitscribe.toml` (project root) controls everything project-specific. Run `git scribe init` to write a starter config. Key sections:

```toml
[rules]
# Markdown files describing your project's commit conventions.
# First found is injected into the LLM prompt.
search = [
  ".cursor/rules/git-commit.mdc",
  ".gitscribe/rules.md",
  "COMMIT_GUIDELINES.md",
]

[scope]
# Directory prefix → scope name. First match wins.
mappings = [
  { prefix = "src/api/", scope = "api" },
  { prefix = "docs/",    scope = "docs" },
]

[type]
# Glob-based fallback type inference.
docs_globs  = ["docs/**", "**/*.md"]
ci_globs    = [".github/**", ".gitlab-ci.yml"]
test_globs  = ["**/tests/**", "**/*.spec.*", "**/*.test.*"]
build_globs = [
  "package.json", "pnpm-lock.yaml",
  "composer.json", "composer.lock",
  "pyproject.toml", "uv.lock",
  "go.mod", "Cargo.toml", "Gemfile",
]
fallback = "chore"

[push]
enabled    = true
require_gh = false
```

## Workflow

1. Collect changes (prefer staged when `--prefer-staged`)
2. Build prompt: rules markdown + changed files + `diff --stat` + patch
3. Call configured LLM CLI (or local heuristic if `--no-llm` / fallback)
4. Open `$EDITOR` for human review (`GIT_EDITOR` → `VISUAL` → `EDITOR` → `vi`)
5. Validate first line matches Conventional Commits
6. `git commit -F` then `git push`

## License

MIT
