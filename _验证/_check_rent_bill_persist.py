# -*- coding: utf-8 -*-
import json
import urllib.request
import pymysql

B = 'http://192.168.31.11:8080/api/v1'


def call(path, method='GET', body=None, token=None):
    data = json.dumps(body).encode() if body is not None else (b'' if method == 'POST' else None)
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': '350600'}
    if token:
        h['Authorization'] = 'Bearer ' + token
    req = urllib.request.Request(B + path, data=data, method=method, headers=h)
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


tok = call('/auth/login', 'POST',
           {'tenantId': '350600', 'username': 'admin', 'password': 'admin123'})['data']['token']
body = {
    'feeItemId': 374371142242275328,
    'periodStart': '2026-12-01',
    'periodEnd': '2026-12-31',
    'billPeriod': '2026-12',
    'contractIds': [374466995221041152],
    'dryRun': False
}
r = call('/fin/bills/generate', 'POST', body, tok)['data']
print('预览/落库结果', r['totalAmount'], r['items'][0]['amount'], r['items'][0]['explain'])
bill_id = r['items'][0]['billId']
print('billId', bill_id)

c = pymysql.connect(host='192.168.31.153', port=33306, user='root', password='5677@Mysql',
                    database='bp_platform', charset='utf8mb4', autocommit=True,
                    connect_timeout=20, read_timeout=60)
cur = c.cursor()
cur.execute('select bill_amount, discount_amount, payable_amount, paid_amount '
            'from bp_fin_bill where id=%s', (bill_id,))
print('账单 应收/减免/待缴/已收 =', cur.fetchone())
# 清理测试账单
cur.execute('delete from bp_fin_bill where id=%s', (bill_id,))
print('已清理测试账单', cur.rowcount)
c.close()
