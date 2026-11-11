#!/usr/bin/env bash
set -euo pipefail
: "${DB_NAME:=bp_platform_v2}"
: "${DB_USER:=bp_platform}"
: "${DB_PASSWORD:?DB_PASSWORD is required}"
: "${1:?usage: restore-db.sh backup.sql.gz}"
backup="$1"
[ -f "$backup" ] || { echo "backup not found: $backup" >&2; exit 1; }
read -r -p "Restore $backup into $DB_NAME? type RESTORE: " ok
[ "$ok" = "RESTORE" ] || exit 1
MYSQL_PWD="$DB_PASSWORD" mysql -u"$DB_USER" "$DB_NAME" < <(gzip -dc "$backup")
echo "restored: $backup"
