#!/usr/bin/env bash
set -euo pipefail

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: Not inside a git repository." >&2
  exit 1
fi

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

if [[ ! -f ".githooks/pre-commit" ]]; then
  echo "ERROR: .githooks/pre-commit not found." >&2
  exit 1
fi

chmod +x .githooks/pre-commit
git config core.hooksPath .githooks

echo "Installed git hooks path: $(git config --get core.hooksPath)"
if [[ -x .githooks/pre-commit ]]; then
  echo "pre-commit hook is executable: yes"
else
  echo "pre-commit hook is executable: no"
  exit 1
fi
