# git-cc

AI-assisted Conventional Commits CLI. Generate a commit message from your diff, review it in `$EDITOR`, then commit and push — in one command.

> 日本語版: [README.ja.md](README.ja.md)

## What it does

git-cc automates the most repetitive part of using Git: writing well-structured commit messages. It reads your working tree changes, asks an LLM (or a local heuristic) to draft a Conventional Commits message that follows **your project's** rules, opens `$EDITOR` so you can review and edit, validates the result, and finally commits and pushes.

The tool is built around two principles:

- **Language-agnostic** (programming language) — works for Python, PHP, TypeScript, Go, Rust, etc. All project-specific behavior (scope mappings, type globs, commit conventions) lives in `.gitcc.toml`, never in the tool's source code.
- **LLM-agnostic** — the LLM is invoked as an external CLI command. Default is `claude`, but you can swap in `cursor`, `codex`, `llm`, `ollama`, or any other CLI by editing one config line.

## How it works

When you run `git cc`, it walks through these steps:

1. **Collect changes** — staged + unstaged + untracked files (use `--prefer-staged` to look only at staged)
2. **Build the prompt** — combines your commit rules + changed file list + `diff --stat` + the full patch
3. **Call the LLM** — runs the CLI you configured (`claude` by default). Falls back to local heuristics if the call fails (unless `[llm].required = true`)
4. **Open `$EDITOR`** — for human review (`GIT_EDITOR` → `VISUAL` → `EDITOR` → `vi`)
5. **Validate** — first line must match Conventional Commits format
6. **Commit and push** — via `git commit -F` then `git push`

---

## 1. Install

If you don't have [uv](https://docs.astral.sh/uv/) yet, install it first:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then install git-cc:

```bash
uv tool install --from "git+https://github.com/ookuni-asset/git-cc.git" git-cc
```

After install, both `git-cc` and `git cc` work — Git auto-discovers `git-*` binaries on `PATH`.

Verify your environment:

```bash
git cc doctor
```

### Updating

```bash
uv tool upgrade git-cc
```

---

## 2. Usage

`git cc` is installed once but run **from inside each repo**, the same way `git` itself works — `cd` into the project you want to commit, then run it. Per-project settings live in `.gitcc.toml`; personal cross-project defaults can go in `~/.config/git-cc/config.toml`.

### Quick start

```bash
cd your-project
git cc init           # creates .gitcc.toml + COMMIT_GUIDELINES.md
git add -A
git cc                # generate → review → commit → push
```

### Commands

| Command / flag | Effect |
|---|---|
| `git cc` | Run the main flow |
| `git cc -a` | Stage everything (`git add -A`) before generating |
| `git cc --prefer-staged` | When something is staged, generate from the staged diff only |
| `git cc --issue 123` | Append `#123` to the subject |
| `git cc --no-push` | Commit only, do not push |
| `git cc --no-llm` | Skip LLM, use heuristic fallback only |
| `git cc --dry-run` | Show the message but do not commit |
| `git cc --lang ja` | Override output language for this run |
| `git cc --llm-command "cursor agent --print {prompt}"` | Override LLM backend for this run |
| `git cc print` | Generate and print, no commit |
| `git cc init` | Bootstrap `.gitcc.toml` + `COMMIT_GUIDELINES.md` |
| `git cc init --cursor` | Also install Cursor rule / skill files |
| `git cc config` | Print the resolved configuration (debug) |
| `git cc doctor` | Check git / LLM / config readiness |

---

## 3. Configuration

Project-specific behavior lives in `.gitcc.toml` at the repo root. Run `git cc init` to write a starter file with comments.

### Pick your LLM (`[llm]`)

git-cc shells out to whatever CLI you point it at. Default is `claude`:

```toml
[llm]
command     = "claude"        # Claude (default)
timeout_sec = 60
required    = false
```

**Switch to Cursor:**

```toml
[llm]
command = "cursor agent --print {prompt}"
```

When the command contains `{prompt}`, it is substituted in place; otherwise the prompt is sent on stdin.

Override per-invocation with env vars:

```bash
GIT_CC_LLM_COMMAND="cursor agent --print {prompt}" git cc
GIT_CC_LLM_TIMEOUT_SEC=120                         git cc
```

### Point to your team's commit rules (`[rules]`)

```toml
[rules]
# First file found is injected verbatim into the LLM prompt.
search = [
  ".cursor/rules/git-commit.mdc",
  ".gitcc/rules.md",
  "COMMIT_GUIDELINES.md",
]
```

If none of the candidates exist in the repo, git-cc falls back to its bundled `default-rules.md`.

### Set the output language (`[language]`)

```toml
[language]
output_lang = "en"   # or "ja", or any code your LLM understands
```

Override per run with `git cc --lang ja`.

### Tune the heuristic fallback (`[scope]` / `[type]`)

These only matter when the LLM is unavailable or you pass `--no-llm`:

```toml
[scope]
mappings = [
  { prefix = "src/api/", scope = "api" },
  { prefix = "docs/",    scope = "docs" },
]

[type]
docs_globs  = ["docs/**", "**/*.md"]
ci_globs    = [".github/**", ".gitlab-ci.yml"]
test_globs  = ["**/tests/**", "**/*.spec.*", "**/*.test.*"]
build_globs = ["package.json", "pyproject.toml", "go.mod", "Cargo.toml"]
fallback = "chore"
```

### Push behavior (`[push]`)

```toml
[push]
enabled    = true
require_gh = false
```

### Configuration layering

git-cc merges configuration bottom-up. Later layers override earlier ones:

1. **Bundled defaults** — `templates/default-config.toml`
2. **User config** — `~/.config/git-cc/config.toml` (or `$XDG_CONFIG_HOME/git-cc/config.toml`)
3. **Project config** — `.gitcc.toml` at the repo root (or `--config <path>`)
4. **Env vars** — `GIT_CC_LLM_COMMAND`, `GIT_CC_LLM_TIMEOUT_SEC`
5. **CLI flags** — `--llm-command`, `--llm-timeout-sec`, `--lang`, `--llm-required`, etc.

Run `git cc config` to inspect the resolved values for the current repo.

---

## License

MIT — see `LICENSE`.
