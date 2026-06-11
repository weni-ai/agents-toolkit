#!/usr/bin/env bash
# Git extension: submit-stack.sh
# Submit the current branch (and its stack) as pull requests using the
# Graphite CLI (gt). Falls back to a plain git push when gt is unavailable.
#
# Usage: submit-stack.sh [--draft]

set -e

DRAFT=false
for arg in "$@"; do
    case "$arg" in
        --draft) DRAFT=true ;;
        --help|-h)
            echo "Usage: $0 [--draft]"
            echo ""
            echo "Submits the current Graphite stack as pull requests (gt submit --stack)."
            echo "Falls back to 'git push -u origin HEAD' when gt is not available."
            exit 0
            ;;
    esac
done

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

_find_project_root() {
    local dir="$1"
    while [ "$dir" != "/" ]; do
        if [ -d "$dir/.specify" ] || [ -d "$dir/.git" ]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    return 1
}

REPO_ROOT=$(_find_project_root "$SCRIPT_DIR") || REPO_ROOT="$(pwd)"
cd "$REPO_ROOT"

if ! command -v git >/dev/null 2>&1; then
    echo "[specify] Warning: Git not found; cannot submit" >&2
    exit 0
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "[specify] Warning: Not a Git repository; cannot submit" >&2
    exit 0
fi

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Returns 0 when the Graphite CLI is available and initialized for this repo
_has_graphite() {
    command -v gt >/dev/null 2>&1 || return 1
    local git_dir
    git_dir=$(git rev-parse --git-common-dir 2>/dev/null) || return 1
    [ -f "$git_dir/.graphite_repo_config" ]
}

if _has_graphite; then
    GT_ARGS=(submit --stack --no-interactive --no-edit)
    if [ "$DRAFT" = true ]; then
        GT_ARGS+=(--draft)
    fi
    if gt_out=$(gt "${GT_ARGS[@]}" 2>&1); then
        printf '%s\n' "$gt_out"
        echo "[OK] Stack submitted with Graphite from branch '$CURRENT_BRANCH'" >&2
        exit 0
    fi
    printf '%s\n' "$gt_out" >&2
    if printf '%s' "$gt_out" | grep -qiE 'auth|token|log ?in'; then
        echo "[specify] Graphite is not authenticated. Run 'gt auth' once, then retry." >&2
        echo "[specify] Falling back to plain git push for the current branch." >&2
    else
        echo "[specify] Warning: gt submit failed; falling back to plain git push." >&2
    fi
fi

# Fallback: push current branch only and ask the user to open the PR manually
if push_out=$(git push -u origin "$CURRENT_BRANCH" 2>&1); then
    printf '%s\n' "$push_out"
    echo "[OK] Branch '$CURRENT_BRANCH' pushed to origin" >&2
    echo "[specify] Graphite unavailable: open the pull request manually (e.g. 'gh pr create' or GitHub UI)" >&2
else
    printf '%s\n' "$push_out" >&2
    echo "[specify] Error: failed to push branch '$CURRENT_BRANCH' to origin" >&2
    exit 1
fi
