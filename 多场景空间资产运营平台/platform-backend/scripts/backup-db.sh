#!/usr/bin/env bash
set -euo pipefail

DB_HOST="${DB_HOST:-192.168.31.153}"
DB_PORT="${DB_PORT:-33306}"
DB_USER="${DB_USER:-root}"
DB_NAME="${DB_NAME:-bp_platform_v2}"
DB_PASSWORD="${DB_PASSWORD:?DB_PASSWORD is required}"
BACKUP_DIR="${BACKUP_DIR:-/home/luo/bp-platform-new/backup}"
KEEP_DAYS="${KEEP_DAYS:-14}"

mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="$BACKUP_DIR/${DB_NAME}_${STAMP}.sql.gz"

if command -v mysqldump >/dev/null 2>&1; then
  mysqldump \
    --single-transaction \
    --routines \
    --triggers \
    --set-gtid-purged=OFF \
    -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" \
    "$DB_NAME" | gzip > "$OUT"
else
  # 无 mysqldump 时使用 JDBC 逻辑备份工具
  BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
  DRIVER="$BASE_DIR/mysql-connector-j-8.3.0.jar"
  if [ ! -f "$DRIVER" ] || [ ! -f "$BASE_DIR/DbBackup.class" ]; then
    echo "mysqldump missing and JDBC backup tool not assembled" >&2
    exit 3
  fi
  RAW="${OUT%.gz}"
  java -cp "$DRIVER:$BASE_DIR" DbBackup \
    "$DB_HOST" "$DB_PORT" "$DB_USER" "$DB_PASSWORD" "$DB_NAME" "$RAW"
  gzip -f "$RAW"
fi

test -s "$OUT"
echo "backup: $OUT ($(du -h "$OUT" | cut -f1))"

find "$BACKUP_DIR" -type f -name "${DB_NAME}_*.sql.gz" -mtime +"$KEEP_DAYS" -delete
