#!/usr/bin/env bash
# Install or upgrade git-scribe. Bootstraps `uv` if missing so the user does
# not need a pre-existing Python toolchain. Source is fetched from GitHub, so
# no local clone is required — this script is safe to pipe from `curl`.
#
# After this runs, future updates are a single command:
#     uv tool upgrade git-scribe
set -e

REPO_URL="git+https://github.com/ookuni-asset/git-scribe.git"

if ! command -v uv >/dev/null 2>&1; then
  echo "==> uv not found, installing from astral.sh..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # uv installs to ~/.local/bin by default; surface it for the rest of this script.
  export PATH="$HOME/.local/bin:$PATH"
fi

echo "==> Installing git-scribe from $REPO_URL"
uv tool install --from "$REPO_URL" git-scribe --force

cat <<'EOM'

==> Done.

Verify the install:
    git scribe doctor

Future updates (no clone needed):
    uv tool upgrade git-scribe

If `git scribe` is not found, add uv's tool dir to your PATH:
    export PATH="$HOME/.local/bin:$PATH"
EOM
