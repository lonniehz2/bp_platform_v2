#!/usr/bin/env bash
set -euo pipefail
: "${BASE_URL:?BASE_URL is required}"
: "${PLATFORM_USER:=admin}"
: "${PLATFORM_PASSWORD:?PLATFORM_PASSWORD is required}"
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
start=$(date +%s%3N)
curl -fsS -X POST "$BASE_URL/api/v1/auth/login" -H 'Content-Type: application/json'   -d "{"tenantCode":"350600","username":"$PLATFORM_USER","password":"$PLATFORM_PASSWORD"}" > "$tmp"
token=$(node -e "const fs=require('fs');const j=JSON.parse(fs.readFileSync('$tmp','utf8'));if(!j.data)process.exit(1);console.log(j.data.token)")
curl -fsS "$BASE_URL/api/v1/auth/menu-tree?sceneCode=GUARANTEE" -H "Authorization: Bearer $token" >/dev/null
curl -fsS "$BASE_URL/api/v1/platform/projects" -H "Authorization: Bearer $token" >/dev/null
end=$(date +%s%3N)
echo "smoke ok: $((end-start)) ms"
