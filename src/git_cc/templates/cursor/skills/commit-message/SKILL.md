---
name: commit-message
description: Generate Conventional Commits messages (type/scope/subject + Why-focused body) by analyzing staged/unstaged git diffs and changed files. Use when the user asks to write a git commit message, "git comment", Conventional Commits, or when running `git scribe`.
---

# Commit message generator (Conventional Commits)

This project uses Conventional Commits. Follow `.cursor/rules/git-commit.mdc`
(or `COMMIT_GUIDELINES.md` if present).

## Goal

Given code changes (prefer staged), output a commit message in this format:

```text
<type>(<scope>): <subject> #<issue>

<body>
```

- `type`: required (`feat|fix|docs|refactor|test|chore|build|ci|perf|style`)
- `scope`: optional (project-specific; check `.gitscribe.toml` `[scope].mappings`)
- `subject`: required, short, no trailing period
- `#<issue>`: optional, only when working by issue
- `body`: optional but **required when Why matters** (especially config / `.gitignore`)

## Workflow

1. Collect change inputs.
   - Prefer staged diff when available.
   - Collect: changed files list, `diff --stat`, and the diff itself.
   - For concrete commands, see `reference.md`.
2. Infer `scope` from paths.
   - Check `.gitscribe.toml` `[scope].mappings` first.
   - Common conventions: docs-only → `docs`, CI-only → `ci`, config-only → `config`.
3. Infer `type`.
   - docs-only → `docs`
   - CI-only → `ci`
   - User-facing behavior added → `feat`
   - Bug fix → `fix`
   - Non-functional restructuring → `refactor`
   - Tooling/scripts/config tweaks → `chore` (or `build` if dependency-related)
4. Write `subject`.
   - ~50 chars, factual, no period.
   - Avoid vague phrases like "変更を反映".
5. Write `body` as bullets, focusing on **Why** (not what).
   - 1 line = 1 topic, prefix `- `.
   - For `.vscode/*` / `.cursor/*` / `.gitignore` changes, always state the reason.
6. Validate.
   - First line matches: `<type>(<scope>): <subject>` (scope omitted is OK).
   - No trailing `。` or `.` in the subject.
   - If config/ignore is changed and body is empty, add Why bullets.

## Output rules

- Output the final commit message **only**, as plain text (no markdown fences).
- If the diff has multiple unrelated themes, pick the dominant one; reflect
  secondary items in the body.
