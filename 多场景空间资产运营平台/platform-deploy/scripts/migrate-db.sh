#!/usr/bin/env bash
set -euo pipefail
: "${DB_NAME:=bp_platform_v2}"
: "${DB_USER:=bp_platform}"
: "${DB_PASSWORD:?DB_PASSWORD is required}"
: "${MIGRATION_DIR:=./platform-sql}"
[ -d "$MIGRATION_DIR" ] || { echo "migration dir not found: $MIGRATION_DIR" >&2; exit 1; }
read -r -p "Apply migrations to $DB_NAME? type MIGRATE: " ok
[ "$ok" = "MIGRATE" ] || exit 1
for f in "$MIGRATION_DIR"/*.sql; do
  echo "apply $(basename "$f")"
  MYSQL_PWD="$DB_PASSWORD" mysql --default-character-set=utf8mb4 -u"$DB_USER" "$DB_NAME" < "$f"
done
echo "migrations applied"
