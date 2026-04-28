# Git commit message rules

This document is the language-agnostic default used by `git-scribe` when no
project-specific rules file is found.

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
