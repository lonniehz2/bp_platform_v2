#!/usr/bin/env bash
set -euo pipefail
: "${DB_NAME:=bp_platform_v2}"
: "${DB_USER:=bp_platform}"
: "${DB_PASSWORD:?DB_PASSWORD is required}"
: "${BACKUP_DIR:=/opt/bp-platform/backups}"
mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"
file="$BACKUP_DIR/${DB_NAME}_$(date +%Y%m%d_%H%M%S).sql.gz"
MYSQL_PWD="$DB_PASSWORD" mysqldump --single-transaction --routines --triggers --events   -u"$DB_USER" "$DB_NAME" | gzip > "$file"
chmod 600 "$file"
find "$BACKUP_DIR" -name '*.sql.gz' -mtime +14 -delete
echo "backup: $file"
