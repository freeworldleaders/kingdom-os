#!/usr/bin/env bash
set -euo pipefail
PROJECT_ID="${PROJECT_ID:-YOUR_PROJECT_ID}"

gcloud logging metrics create dlp_gemini_dlp_matches \
  --description="DLP matches triggered by Gemini interactions" \
  --log-filter="resource.type=\"gce_instance\" OR protoPayload.methodName:\"DlpJob\" OR textPayload:\"DLP match\"" \
  --project="${PROJECT_ID}"
