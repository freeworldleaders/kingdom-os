#!/usr/bin/env bash
set -eo pipefail

DATABASE_URL="${DATABASE_URL:-}"
SCRIPT_PATH=""
DRY_RUN=0
EXECUTE=0
BACKUP_BEFORE=1

function usage() {
  cat <<EOF
Usage: $0 --database-url <URL> --script <roles_sql> [--dry-run | --execute] [--no-backup]
EOF
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --database-url) DATABASE_URL="$2"; shift 2;;
    --script) SCRIPT_PATH="$2"; shift 2;;
    --dry-run) DRY_RUN=1; shift;;
    --execute) EXECUTE=1; shift;;
    --no-backup) BACKUP_BEFORE=0; shift;;
    --help) usage;;
    *) echo "Unknown arg: $1"; usage;;
  esac
done

if [[ -z "$DATABASE_URL" || -z "$SCRIPT_PATH" ]]; then
  echo "ERROR: --database-url and --script required"
  usage
fi

if (( DRY_RUN && EXECUTE )); then
  echo "ERROR: choose one of --dry-run or --execute"
  exit 1
fi

if (( !DRY_RUN && !EXECUTE )); then
  DRY_RUN=1
fi

if (( BACKUP_BEFORE )); then
  TS=$(date -u +"%Y%m%dT%H%M%SZ")
  BACKUP_FILE="roles_backup_${TS}.sql"
  echo "Backing up roles and devices_history to $BACKUP_FILE"
  pg_dump --table=roles --table=devices_history --data-only --column-inserts "$DATABASE_URL" -f "$BACKUP_FILE"
  gsutil cp "$BACKUP_FILE" gs://kingdom-os-artifacts/backups/ || echo "Warning: upload failed"
fi

if (( DRY_RUN )); then
  echo "DRY-RUN: executing roles script inside a transaction"
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 <<PSQL
BEGIN;
\i '$SCRIPT_PATH';
ROLLBACK;
PSQL
  echo "Dry-run complete."
else
  echo "EXECUTE: applying roles script"
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$SCRIPT_PATH"
  echo "Roles applied."
fi
