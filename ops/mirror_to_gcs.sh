#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-YOUR_PROJECT_ID}"
BUCKET="${BUCKET:-kingdom-os-artifacts}"
REPO_URL="${REPO_URL:-https://github.com/freeworldleaders/kingdom-os.git}"
TMPDIR="/tmp/kingdom_mirror"

rm -rf "$TMPDIR"
git clone --mirror "$REPO_URL" "$TMPDIR"
TS=$(date -u +"%Y%m%dT%H%M%SZ")
git -C "$TMPDIR" bundle create "/tmp/kingdom-os-${TS}.bundle" --all
gsutil cp "/tmp/kingdom-os-${TS}.bundle" "gs://${BUCKET}/backups/"
echo "Uploaded bundle to gs://${BUCKET}/backups/kingdom-os-${TS}.bundle"
