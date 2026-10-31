# -*- coding: utf-8 -*-
import json
import time
import urllib.request
import urllib.error

import pymysql

B = 'http://192.168.31.11:8080/api/v1'
POINT = 1793419865712010
ELEC = 371722116640411648


def call(path, method='GET', body=None, token=None):
    data = json.dumps(body).encode() if body is not None else (b'' if method == 'POST' else None)
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': '350600'}
    if token:
        h['Authorization'] = 'Bearer ' + token
    req = urllib.request.Request(B + path, data=data, method=method, headers=h)
    try:
        return urllib.request.urlopen(req, timeout=60).read().decode()
    except urllib.error.HTTPError as e:
        return 'HTTP%d %s' % (e.code, e.read().decode()[:120])


tok = json.loads(call('/auth/login', 'POST',
                       {'tenantId': '350600', 'username': 'admin',
                        'password': 'admin123'}))['data']['token']

print('read-now:', call('/fin/meter-points/%s/read-now' % POINT, 'POST', {}, tok)[:120])
print('manual:', call('/fin/meter-points/%s/readings' % POINT, 'POST',
                      {'reading': 500, 'readTime': '2026-11-30T23:59:00',
                       'remark': 'M3人工抄表'}, tok)[:120])

c = pymysql.connect(host='192.168.31.153', port=33306, user='root', password='5677@Mysql',
                    database='bp_platform', charset='utf8mb4', autocommit=True,
                    connect_timeout=20, read_timeout=60)
cur = c.cursor()
cur.execute("update bp_biz_contract set lease_end='2026-11-30' where id in (1793419865258001,1793419865332002)")
# 11 月期初读数
cur.execute("""insert into bp_fin_meter_point_reading
 (id,tenant_id,meter_point_id,reading,read_time,source,create_time)
 values (%s,'350600',%s,400,'2026-11-01 00:00:00','MANUAL',now(3))""",
            (int(time.time() * 1000) * 1000 + 70, POINT))
c.close()

rule = {
    'ruleCode': 'M4-ELEC-TIER', 'ruleName': 'M4阶梯电价', 'feeItemId': ELEC,
    'ruleType': 'TIERED',
    'priceConfig': '{"tiers":[{"limit":50,"price":0.5},{"limit":null,"price":0.6}]}',
    'effectiveStart': '2026-01-01', 'priority': 100
}
print('rule:', call('/fin/billing-rules', 'POST', rule, tok)[:160])
print('preview:', call('/fin/utility-allocations/preview', 'POST',
                       {'period': '2026-11', 'meterPointId': POINT}, tok)[:400])
