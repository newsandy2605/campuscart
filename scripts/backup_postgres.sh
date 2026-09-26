#!/usr/bin/env bash
set -euo pipefail
: "${DATABASE_URL:?Set DATABASE_URL}"
out_dir="${BACKUP_DIR:-./backups}"
mkdir -p "$out_dir"
file="$out_dir/campuscart-$(date +%Y%m%d-%H%M%S).dump"
pg_dump "$DATABASE_URL" --format=custom --file="$file"
echo "$file"
