# Git commit message rules

This document is the language-agnostic default used by `git-scribe` when no
project-specific rules file is found.

## Language

Write the commit message in the **same natural language used to write this
rules document**. (To switch languages for your project, run
`git scribe init` and translate `COMMIT_GUIDELINES.md` — the LLM will then
follow that language deterministically.)

## Format

```
<type>(<scope>): <subject> #<issue>

<body>
```

- **type**: required (`feat|fix|docs|refactor|test|chore|build|ci|perf|style`)
- **scope**: optional (e.g. `api`, `web`, `docs`, `deps`, `config`)
- **subject**: required, one short line, no trailing period
- **#<issue>**: optional; append `#123` when working on an issue
- **body**: optional, but **required when Why matters**

## type

- `feat`: new user-visible feature
- `fix`: bug fix
- `docs`: documentation only
- `refactor`: behavior-preserving restructuring
- `test`: tests added or updated
- `chore`: misc maintenance / tooling
- `build`: build system or dependency change
- `ci`: CI configuration
- `perf`: performance improvement
- `style`: formatting only (whitespace etc.)

## subject rules

- No trailing period (`。` or `.`)
- About 50 characters
- Describe what was done, factually

### Subject focus when a commit spans multiple topics

When a single commit touches several unrelated areas, the subject must
reflect the **highest-priority** change. Never silently drop the others —
move them to the body.

Priority (high → low):

1. `feat` (new user-visible feature)
2. `fix`
3. `refactor` / `perf`
4. `docs` / `test` / `build` / `ci` / `chore` / `style`

When multiple changes share the priority, name the **broader theme** rather
than the smallest concrete file. For example, prefer
"FastAPI scaffold + editor config" over "add GET / endpoint" when the
commit also introduces VSCode settings and `.gitignore` changes.

## body rules (Why-focused)

The body explains **Why**, not **What** — the diff already shows what.

- Capture environment-drift fixes, operational intent, groundwork for future work
- Config files / `.gitignore` changes **must** explain why
- One bullet per topic, prefixed with `- `

## Examples

### Example 1: feature + config

```
feat(api): add health endpoint

- GET / makes startup verification easy
- Helps frontend tooling probe backend liveness without a real route
```

### Example 2: config only

```
chore(config): pin editor Python interpreter to project venv

- Prevents per-developer drift on analysis/run/debug targets
```

### Example 3: feat with supporting config (mixed-topic commit)

When a commit bundles a feature with the configuration that supports it,
the subject describes the feature; the body covers every topic with Why.

```
feat(api): add FastAPI scaffold with health endpoint

- GET / lets contributors verify the backend boots before real routes are wired
- Pin VSCode Python interpreter to backend/.venv to prevent analysis/debug drift
- Untrack .vscode/ in .gitignore so the shared editor config can be committed
```
