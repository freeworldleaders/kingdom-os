#!/usr/bin/env bash
set -eo pipefail

REPO_DIR="${1:-.}"
APPLY=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply) APPLY=1; shift;;
    *) shift;;
  esac
done

echo "Scanning repo for potential issues..."

echo "Large files (in current tree):"
find "$REPO_DIR" -type f -printf "%s %p\n" | sort -nr | head -n 20

echo "Searching for secret-like strings:"
git -C "$REPO_DIR" grep -n --break --heading -E "BEGIN RSA PRIVATE KEY|PRIVATE KEY|AKIA|AWS_SECRET|SECRET_KEY|PASSWORD|passw" || true

echo "No destructive action will be taken without --apply."
if (( APPLY )); then
  echo "APPLY enabled. Use git-filter-repo or BFG to remove secrets after manual review."
fi
