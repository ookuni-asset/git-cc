#!/usr/bin/env bash
# Run git-scribe on the last N non-merge commits of a target repo and compare
# the generated subject to the original. Prints a summary table and writes a
# TSV plus a full log for detailed inspection.
#
# Usage:  scripts/eval-against-history.sh <repo-path> [N]
# Example: scripts/eval-against-history.sh ../ebay-research-api 10

set -uo pipefail

REPO="${1:-}"
N="${2:-20}"

if [[ -z "$REPO" ]]; then
  echo "usage: $0 <repo-path> [N]" >&2
  exit 2
fi
if [[ ! -d "$REPO/.git" ]]; then
  echo "not a git repo: $REPO" >&2
  exit 2
fi

REPO="$(cd "$REPO" && pwd)"

if ! command -v git-scribe >/dev/null 2>&1; then
  echo "git-scribe not on PATH" >&2
  exit 2
fi

OUT_DIR="$(mktemp -d -t git-scribe-eval.XXXXXX)"
TSV="$OUT_DIR/results.tsv"
LOG="$OUT_DIR/full.log"

echo "repo:    $REPO"
echo "samples: up to $N non-merge commits (root commit excluded)"
echo "output:  $OUT_DIR"
echo

printf 'sha\tstatus\torig_subject\tgen_subject\n' > "$TSV"

SHAS=()
while IFS= read -r sha; do
  if git -C "$REPO" rev-parse --verify -q "${sha}^" >/dev/null 2>&1; then
    SHAS+=("$sha")
  fi
done < <(git -C "$REPO" log --no-merges --pretty=%H -n "$N")

if [[ ${#SHAS[@]} -eq 0 ]]; then
  echo "no eligible commits" >&2
  exit 1
fi

run_one() {
  local sha="$1"
  local parent orig_subj orig_body wt status gen_full gen_subj apply_err

  parent=$(git -C "$REPO" rev-parse "${sha}^")
  orig_subj=$(git -C "$REPO" log -1 --format='%s' "$sha")
  orig_body=$(git -C "$REPO" log -1 --format='%B' "$sha")
  wt="$OUT_DIR/wt-${sha:0:7}"

  status="ok"
  gen_full=""
  gen_subj=""

  if ! git -C "$REPO" worktree add --detach "$wt" "$parent" >/dev/null 2>&1; then
    status="worktree-failed"
  else
    apply_err=$(git -C "$REPO" diff "$parent" "$sha" | git -C "$wt" apply --index --whitespace=nowarn 2>&1 >/dev/null) || true
    if [[ -n "$apply_err" ]]; then
      status="apply-failed"
    else
      if raw_out=$(cd "$wt" && git scribe print --prefer-staged 2>/dev/null); then
        # `git scribe print` also dumps `=== changed files ===` etc. before the
        # message itself. Keep only what follows the message marker.
        gen_full=$(printf '%s\n' "$raw_out" | awk '/^=== generated commit message ===$/{f=1;next} f')
        gen_subj=$(printf '%s\n' "$gen_full" | head -1)
      else
        status="scribe-failed"
      fi
    fi
    git -C "$REPO" worktree remove --force "$wt" >/dev/null 2>&1 || true
  fi

  echo "[$status] $sha"
  echo "  original:  $orig_subj"
  echo "  generated: ${gen_subj:-<no output>}"
  echo

  {
    printf '=== %s (%s) ===\n' "$sha" "$status"
    printf -- '--- ORIGINAL ---\n%s\n\n' "$orig_body"
    printf -- '--- GENERATED ---\n%s\n\n' "${gen_full:-<none>}"
  } >> "$LOG"

  printf '%s\t%s\t%s\t%s\n' \
    "${sha:0:7}" \
    "$status" \
    "$(printf '%s' "$orig_subj" | tr '\t\n' '  ')" \
    "$(printf '%s' "$gen_subj"  | tr '\t\n' '  ')" >> "$TSV"
}

for sha in "${SHAS[@]}"; do
  run_one "$sha"
done

echo "=== summary ==="
if command -v column >/dev/null 2>&1; then
  column -s $'\t' -t < "$TSV"
else
  cat "$TSV"
fi

echo
echo "TSV: $TSV"
echo "log: $LOG  (open this for full original/generated bodies)"
