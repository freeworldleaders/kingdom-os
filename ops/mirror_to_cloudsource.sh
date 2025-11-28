#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-YOUR_PROJECT_ID}"
GITHUB_REPO="${GITHUB_REPO:-https://github.com/freeworldleaders/kingdom-os.git}"

gcloud source repos create kingdom-os --project="${PROJECT_ID}" || true
git clone --mirror "${GITHUB_REPO}" kingdom-os.git
cd kingdom-os.git
git remote add gcloud "https://source.developers.google.com/p/${PROJECT_ID}/r/kingdom-os"
git push --mirror gcloud
echo "Mirrored to Cloud Source Repos"
