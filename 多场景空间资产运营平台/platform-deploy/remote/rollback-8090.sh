#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="${APP_DIR:-/home/luo/bp-platform-new}" APP_PORT=8090 source "$HERE/common.sh"
BACKUP_DIR_SEED="${BACKUP_DIR:-$APP_DIR/backup}"
JAR="${1:-}"
if [ -z "$JAR" ]; then
  JAR=$(ls -1t "$BACKUP_DIR_SEED"/multi-scene-platform.jar.* 2>/dev/null | head -1 || true)
fi
[ -n "$JAR" ] && [ -f "$JAR" ] || { echo "usage: rollback-8090.sh <backup-jar>" >&2; exit 1; }
read -r -p "rollback $APP_DIR to $JAR ? type ROLLBACK: " ok
[ "$ok" = "ROLLBACK" ] || exit 1
PID=$(ss -lntp 2>/dev/null | awk '/:8090 /{print $NF}' | grep -o 'pid=[0-9]*' | cut -d= -f2 | head -1)
[ -n "${PID:-}" ] && kill "$PID" && sleep 3
cp -a "$JAR" "$APP_DIR/multi-scene-platform.jar"
cd "$APP_DIR"
DB_PASSWORD="${DB_PASSWORD:?DB_PASSWORD required}" SERVER_PORT=8090 nohup java -Xms512m -Xmx1024m -XX:+UseG1GC -Dfile.encoding=UTF-8 -jar multi-scene-platform.jar > app.log 2>&1 < /dev/null &
sleep 10
bash "$HERE/verify-8090.sh"
