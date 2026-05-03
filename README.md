# git-scribe

AI-assisted Conventional Commits CLI. Generate a commit message from your diff, review it in `$EDITOR`, then commit and push — in one command.

> 日本語版: [README.ja.md](README.ja.md)

## What it does

git-scribe automates the most repetitive part of using Git: writing well-structured commit messages. It reads your working tree changes, asks an LLM (or a local heuristic) to draft a Conventional Commits message that follows **your project's** rules, opens `$EDITOR` so you can review and edit, validates the result, and finally commits and pushes.

The tool is built around two principles:

- **Language-agnostic** (programming language) — works for Python, PHP, TypeScript, Go, Rust, etc. All project-specific behavior (scope mappings, type globs, commit conventions) lives in `.gitscribe.toml`, never in the tool's source code.
- **LLM-agnostic** — the LLM is invoked as an external CLI command. Default is `claude`, but you can swap in `codex`, `llm`, `ollama`, or any other CLI by editing one config line.

Use it when you want to: stop hand-writing commit titles, enforce Conventional Commits across a team without nagging in PR review, replace an ad-hoc commit-message shell script with a configurable tool, or experiment with different LLM backends (including local models) for the same job.

## How it works

When you run `git scribe`, it walks through these steps:

1. **Collect changes** — staged + unstaged + untracked files (use `--prefer-staged` to look only at staged)
2. **Build the prompt** — combines your commit rules + changed file list + `diff --stat` + the full patch
3. **Call the LLM** — runs the CLI you configured (`claude` by default). Falls back to local heuristics if the call fails (unless `[llm].required = true`)
4. **Open `$EDITOR`** — for human review (`GIT_EDITOR` → `VISUAL` → `EDITOR` → `vi`)
5. **Validate** — first line must match Conventional Commits format
6. **Commit and push** — via `git commit -F` then `git push`

---

## 1. Install

If you don't have [uv](https://docs.astral.sh/uv/) yet, the one-liner below bootstraps uv and then installs git-scribe in one shot — no clone, no Python toolchain required:

```bash
curl -LsSf https://raw.githubusercontent.com/ookuni-asset/git-scribe/main/install.sh | bash
```

If you already have uv, install directly from the public repo URL:

```bash
uv tool install --from "git+https://github.com/ookuni-asset/git-scribe.git" git-scribe
```

Cloning the repo and running `./install.sh` works the same way.

> Windows: install uv via `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`, then run the `uv tool install` command above.

After install, both `git-scribe` and `git scribe` work — Git auto-discovers `git-*` binaries on `PATH`.

Verify your environment:

```bash
git scribe doctor
```

### Updating

```bash
uv tool upgrade git-scribe
```

uv re-fetches the latest commit from GitHub and rebuilds in place. No clone or script needed.

---

## 2. Usage

`git scribe` is installed once but run **from inside each repo**, the same way `git` itself works — `cd` into the project you want to commit, then run it. The tool auto-detects the current repository via `git rev-parse --show-toplevel`. Per-project settings (LLM, rules, scope mappings) live in that repo's `.gitscribe.toml`; personal cross-project defaults can go in `~/.config/git-scribe/config.toml`.

### Quick start

```bash
cd your-project
git scribe init           # creates .gitscribe.toml + COMMIT_GUIDELINES.md
git add -A
git scribe                # generate → review → commit → push
```

### Commands

`git scribe` with no subcommand defaults to the main flow.

| Command / flag | Effect |
|---|---|
| `git scribe` | Run the main flow |
| `git scribe -a` | Stage everything (`git add -A`) before generating |
| `git scribe --prefer-staged` | When something is staged, generate from the staged diff only (ignore unstaged/untracked) |
| `git scribe --issue 123` | Append `#123` to the subject |
| `git scribe --no-push` | Commit only, do not push |
| `git scribe --no-llm` | Skip LLM, use heuristic fallback only |
| `git scribe --dry-run` | Show the message but do not commit |
| `git scribe --lang ja` | Override output language for this run |
| `git scribe --llm-command "ollama run qwen2.5-coder:7b"` | Override LLM backend for this run |
| `git scribe print` | Generate and print, no commit |
| `git scribe init` | Bootstrap `.gitscribe.toml` + `COMMIT_GUIDELINES.md` |
| `git scribe init --cursor` | Also install Cursor rule / skill files |
| `git scribe config` | Print the resolved configuration (debug) |
| `git scribe doctor` | Check git / LLM / config readiness |

---

## 3. Configuration

Project-specific behavior lives in `.gitscribe.toml` at the repo root. Run `git scribe init` to write a starter file with comments.

### Pick your LLM (`[llm]`)

git-scribe shells out to whatever CLI you point it at. Default is `claude`:

```toml
[llm]
command     = "claude"        # or "codex exec {prompt}", "llm -m gpt-4o", "ollama run qwen2.5-coder:7b", ...
timeout_sec = 60
required    = false           # if true, exit with error when the LLM call fails (no heuristic fallback)
```

When the command contains `{prompt}`, it is substituted in place; otherwise the prompt is sent on stdin.

Override per-invocation with env vars:

```bash
GIT_SCRIBE_LLM_COMMAND="ollama run qwen2.5-coder:7b" git scribe
GIT_SCRIBE_LLM_TIMEOUT_SEC=120                       git scribe
```

### Point to your team's commit rules (`[rules]`)

```toml
[rules]
# First file found is injected verbatim into the LLM prompt.
search = [
  ".cursor/rules/git-commit.mdc",
  ".gitscribe/rules.md",
  "COMMIT_GUIDELINES.md",
]
```

If none of the candidates exist in the repo, git-scribe falls back to its bundled `default-rules.md`.

### Set the output language (`[language]`)

```toml
[language]
output_lang = "en"   # or "ja", or any code your LLM understands
```

Override per run with `git scribe --lang ja`.

### Tune the heuristic fallback (`[scope]` / `[type]`)

These only matter when the LLM is unavailable or you pass `--no-llm`:

```toml
[scope]
# Directory prefix → scope name. First match wins.
mappings = [
  { prefix = "src/api/", scope = "api" },
  { prefix = "docs/",    scope = "docs" },
]

[type]
# Glob-based type inference for the heuristic generator.
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
```

### Push behavior (`[push]`)

```toml
[push]
enabled    = true     # set false to make `git scribe` commit-only by default
require_gh = false    # if true, run `gh repo set-default / auth status / repo sync` before push
```

### Configuration layering

git-scribe merges configuration bottom-up. Later layers override earlier ones:

1. **Bundled defaults** — `templates/default-config.toml` (the single source of truth for defaults)
2. **User config** — `~/.config/git-scribe/config.toml` (or `$XDG_CONFIG_HOME/git-scribe/config.toml`)
3. **Project config** — `.gitscribe.toml` at the repo root (or `--config <path>`)
4. **Env vars** — `GIT_SCRIBE_LLM_COMMAND`, `GIT_SCRIBE_LLM_TIMEOUT_SEC`
5. **CLI flags** — `--llm-command`, `--llm-timeout-sec`, `--lang`, `--llm-required`, etc.

Run `git scribe config` to inspect the resolved values for the current repo.

---

## License

MIT — see `LICENSE`.
