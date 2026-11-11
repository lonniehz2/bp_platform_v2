#!/usr/bin/env bash
set -euo pipefail
: "${AUTH_SECRET:?AUTH_SECRET is required}"
: "${DB_PASSWORD:?DB_PASSWORD is required}"
fail=0
[ "${#AUTH_SECRET}" -ge 32 ] || { echo "AUTH_SECRET too short"; fail=1; }
case "$AUTH_SECRET" in *dev-only-change-me*) echo "AUTH_SECRET is default"; fail=1;; esac
case "$DB_PASSWORD" in *local123*|*CHANGE_ME*) echo "DB_PASSWORD is weak/default"; fail=1;; esac
case "${CORS_ALLOWED_ORIGINS:-}" in *"*"*) echo "CORS_ALLOWED_ORIGINS must not contain *"; fail=1;; esac
[ -d /opt/bp-platform/uploads ] || { echo "uploads dir missing"; fail=1; }
stat -c '%a' /etc/bp-platform.env 2>/dev/null | grep -q '^600$' || { echo "/etc/bp-platform.env must be chmod 600"; fail=1; }
ss -lntp 2>/dev/null | grep -q ':8091 ' && echo "notice: 8091 must not be public"
[ "$fail" -eq 0 ] && echo "security-check: ok"
exit "$fail"
