## Suggested data collection

Use these commands to gather inputs before drafting the message:

```bash
git diff --name-only --staged
git diff --stat --staged
git diff --staged
```

If nothing is staged, fall back to unstaged:

```bash
git diff --name-only
git diff --stat
git diff
```

If both exist and the user is about to commit, prefer staged to avoid
describing uncommitted noise.

## Heuristics (project conventions)

- `.vscode/` or `.cursor/` changes:
  - Scope is usually `config`
  - Body must explain why (environment drift, interpreter mismatch, etc.)
- `.gitignore` changes:
  - Body must explain why (what problem was observed/likely)
- `docs/`-only changes:
  - Type should be `docs`
  - Scope can be `docs` (or omitted if mixed docs)
