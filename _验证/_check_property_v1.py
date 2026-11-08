# -*- coding: utf-8 -*-
"""智慧物业 V1 核心接口回归。"""
import json
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080/api/v1'
PROJECT = '370988445033697280'


def call(path, method='GET', body=None, token=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header('Content-Type', 'application/json')
    if token:
        req.add_header('Authorization', 'Bearer ' + token)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def main():
    status, body = call('/auth/login', 'POST', {
        'tenantId': '350600', 'username': 'admin', 'password': 'admin123'})
    assert status == 200, body
    token = body['data']['token']
    checks = [
        ('项目', '/property/projects'),
        ('分类', '/property/categories?type=INCOME'),
        ('收费项目', '/property/fee-items?projectId=' + PROJECT),
        ('账单', '/property/bills?projectId=' + PROJECT + '&pageSize=5'),
        ('收据', '/property/receipts?projectId=' + PROJECT),
        ('车位', '/property/parking/spaces?projectId=' + PROJECT),
        ('车位价格', '/property/parking/rates?projectId=' + PROJECT),
        ('物业房屋', '/property/units?projectId=' + PROJECT),
        ('业主', '/property/units/' + '376663347237621760' + '/owners?projectId=' + PROJECT),
        ('支出', '/property/expenses?projectId=' + PROJECT + '&month=2026-11'),
        ('经营报表', '/property/reports/overview?projectId=' + PROJECT + '&month=2026-11'),
        ('欠费', '/property/dunning/arrears?projectId=' + PROJECT),
        ('催缴任务', '/property/dunning/tasks?projectId=' + PROJECT),
        ('公摊能耗', '/property/energy/allocations?projectId=' + PROJECT + '&period=2026-11'),
        ('水电表', '/property/meters?projectId=' + PROJECT),
        ('抄表记录', '/property/meters/readings?projectId=' + PROJECT),
        ('电子发票', '/property/invoices?projectId=' + PROJECT),
    ]
    ok = 0
    for name, path in checks:
        status, body = call(path, token=token)
        passed = status == 200 and body.get('code') == 'BP00000'
        print(('PASS' if passed else 'FAIL'), name, status, body.get('code'))
        ok += 1 if passed else 0
    print('SUMMARY %d/%d' % (ok, len(checks)))
    return 0 if ok == len(checks) else 1


if __name__ == '__main__':
    raise SystemExit(main())
