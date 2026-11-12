#!/usr/bin/env bash
set -euo pipefail
# 仅允许操作 8090 业务平台；8080 老系统绝对不碰。
APP_DIR="${APP_DIR:-/home/luo/bp-platform-new}"
APP_PORT="${APP_PORT:-8090}"
OLD_SYSTEM_DIR="/opt/bp-platform"
OLD_SYSTEM_PORT="8080"
DB_HOST="${DB_HOST:-192.168.31.153}"
DB_PORT="${DB_PORT:-33306}"
DB_NAME="${DB_NAME:-bp_platform_v2}"
DB_USER="${DB_USER:-root}"

[ "$APP_PORT" = "8090" ] || { echo "refuse: APP_PORT must be 8090" >&2; exit 1; }
case "$APP_DIR" in
  "$OLD_SYSTEM_DIR"|"$OLD_SYSTEM_DIR"/*) echo "refuse: old system dir" >&2; exit 1;;
esac
[ -d "$APP_DIR" ] || { echo "missing app dir: $APP_DIR" >&2; exit 1; }
echo "target: $APP_DIR port=$APP_PORT db=$DB_HOST:$DB_PORT/$DB_NAME"
