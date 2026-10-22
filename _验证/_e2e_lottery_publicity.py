# -*- coding: utf-8 -*-
"""端到端造数：批次 → 摇号 → 公示(关联批次) → 中签名单，验证「去签约」数据来源。"""
import json
import urllib.error
import urllib.request

API = 'http://192.168.31.11:8080/api/v1'


def call(path, method='GET', body=None, token=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=data, method=method)
    r.add_header('Content-Type', 'application/json')
    r.add_header('X-Tenant-Id', '350600')
    if token:
        r.add_header('Authorization', 'Bearer ' + token)
    try:
        with urllib.request.urlopen(r, timeout=40) as x:
            return x.status, json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {'message': str(e)}


_, d = call('/auth/login', 'POST',
            {'tenantCode': '350600', 'username': 'admin', 'password': 'admin123'})
tok = d['data']['token']

org = call('/orgs', token=tok)[1]['data']['rows'][0]['id']

st, b = call('/allocation/batches', 'POST',
             {'batchName': '联动测试批次', 'orgId': org,
              'securityType': 'PUBLIC', 'batchType': 'LOTTERY'}, tok)
print('建批次:', st, (b or {}).get('code'))
bid = ((b or {}).get('data') or {}).get('id')
if not bid:
    raise SystemExit('批次创建失败: %s' % (b or {}))

st, h = call('/houses?pageNum=1&pageSize=5&status=VACANT', token=tok)
houses = ((h.get('data') or {}).get('rows') or [])
ids = [x['id'] for x in houses[:2]]
st, hh = call('/allocation/batches/%s/houses' % bid, 'POST', {'houseIds': ids}, tok)
print('加房源:', st, (hh or {}).get('code'), '数量', len(ids))

st, lot = call('/allocation/lottery', 'POST', {'batchId': bid, 'seed': 'demo'}, tok)
print('摇号:', st, (lot or {}).get('code'), (lot or {}).get('message', ''))

st, res = call('/allocation/lottery/%s' % bid, token=tok)
rows = (res.get('data') or []) if isinstance(res, dict) else []
print('摇号结果:', st, '条数', len(rows))

st, pub = call('/publicities', 'POST',
               {'publicityType': 'ALLOCATION', 'orgId': org, 'batchId': bid,
                'title': '联动测试公示', 'content': '中签名单验证',
                'startDate': '2026-01-01', 'endDate': '2026-01-15'}, tok)
print('建公示:', st, (pub or {}).get('code'), (pub or {}).get('message', ''))
pid = ((pub or {}).get('data') or {}).get('id')
if pid:
    st, w = call('/publicities/%s/winners' % pid, token=tok)
    ww = (w.get('data') or []) if isinstance(w, dict) else []
    print('中签名单:', st, '条数', len(ww))
    if ww:
        print('样例:', json.dumps(ww[0], ensure_ascii=False))
