#!/usr/bin/env bash
set -euo pipefail
BASE="${BASE:-http://127.0.0.1:8090}"
USER_NAME="${PLATFORM_USER:-admin}"
PASSWORD="${PLATFORM_PASSWORD:?PLATFORM_PASSWORD is required}"
TOKEN=$(python3 - "$BASE" "$USER_NAME" "$PASSWORD" <<'PY'
import json,sys,urllib.request
base,user,pw=sys.argv[1],sys.argv[2],sys.argv[3]
req=urllib.request.Request(base+'/api/v1/auth/login',data=json.dumps({'tenantCode':'350600','username':user,'password':pw}).encode(),headers={'Content-Type':'application/json'})
with urllib.request.urlopen(req,timeout=15) as r: j=json.load(r)
if j.get('code')!='BP00000': raise SystemExit(j.get('code'))
print(j['data']['token'])
PY
)
python3 - "$BASE" "$TOKEN" <<'PY'
import json,sys,urllib.request
base,token=sys.argv[1],sys.argv[2]
h={'Authorization':'Bearer '+token}
for scene in ('GUARANTEE','ASSET','SERVICE'):
 req=urllib.request.Request(f'{base}/api/v1/auth/menu-tree?sceneCode={scene}',headers=h)
 with urllib.request.urlopen(req,timeout=15) as r: m=json.load(r)
 req=urllib.request.Request(f'{base}/api/v1/platform/roles?sceneCode={scene}',headers=h)
 with urllib.request.urlopen(req,timeout=15) as r: roles=json.load(r)
 print(scene,'menus=',len(m.get('data') or []),'roles=',len(roles.get('data') or []))
 if len(m.get('data') or [])!=10: raise SystemExit('menu count != 10')
 if len(roles.get('data') or [])<4: raise SystemExit('role count < 4')
PY
