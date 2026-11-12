#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="${APP_DIR:-/home/luo/bp-platform-new}" APP_PORT=8090 source "$HERE/common.sh"
: "${DB_PASSWORD:?DB_PASSWORD is required}"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR_SEED="${BACKUP_DIR:-$APP_DIR/backup}"
mkdir -p "$BACKUP_DIR_SEED"
echo "backup database..."
DB_HOST="$DB_HOST" DB_PORT="$DB_PORT" DB_NAME="$DB_NAME" DB_USER="$DB_USER" DB_PASSWORD="$DB_PASSWORD"   BACKUP_DIR="$BACKUP_DIR_SEED" bash "$APP_DIR/backup-db.sh"
echo "backup jar..."
cp -a "$APP_DIR/multi-scene-platform.jar" "$BACKUP_DIR_SEED/multi-scene-platform.jar.$STAMP"
echo "backup complete: $BACKUP_DIR_SEED"
