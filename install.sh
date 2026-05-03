#!/usr/bin/env bash
# Install git-scribe from this repo. Bootstraps `uv` if missing so the user
# does not need a pre-existing Python toolchain — uv will fetch a suitable
# Python interpreter automatically.
set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v uv >/dev/null 2>&1; then
  echo "==> uv not found, installing from astral.sh..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # uv installs to ~/.local/bin by default; surface it for the rest of this script.
  export PATH="$HOME/.local/bin:$PATH"
fi

echo "==> Installing git-scribe from $REPO_DIR"
uv tool install --from "$REPO_DIR" git-scribe --force

cat <<'EOM'

==> Done.

Verify the install:
    git scribe doctor

If `git scribe` is not found, add uv's tool dir to your PATH:
    export PATH="$HOME/.local/bin:$PATH"
EOM
