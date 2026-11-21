#!/usr/bin/env bash
# Configure Git remotes to support pushing to both GitHub and GitLab.
# Usage: bash scripts/setup-remotes.sh <github_repo_url> <gitlab_repo_url>

set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <github_repo_url> <gitlab_repo_url>" >&2
  exit 1
fi

GITHUB_URL="$1"
GITLAB_URL="$2"

git remote remove github >/dev/null 2>&1 || true
git remote remove gitlab >/dev/null 2>&1 || true
git remote add github "$GITHUB_URL"
git remote add gitlab "$GITLAB_URL"

# Configure 'all' remote so a single `git push all main` pushes to both platforms
git remote remove all >/dev/null 2>&1 || true
git remote add all "$GITHUB_URL"
git remote set-url --add --push all "$GITHUB_URL"
git remote set-url --add --push all "$GITLAB_URL"

echo "Configured remotes:"
git remote -v
