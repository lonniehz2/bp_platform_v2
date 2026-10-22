# -*- coding: utf-8 -*-
"""一期示范数据清单：统计该小区下各环节数据，用于验收对照。"""
import json
import urllib.error
import urllib.request

API = 'http://192.168.31.11:8080/api/v1'
ORG = '一期示范小区'


def call(path, token=None):
    r = urllib.request.Request(API + path,
                               headers={'Authorization': 'Bearer ' + (token or ''),
                                        'X-Tenant-Id': '350600'})
    try:
        with urllib.request.urlopen(r, timeout=40) as x:
            return json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        return {'code': 'HTTP%d' % e.code}


def rows(d):
    data = (d or {}).get('data')
    if isinstance(data, dict):
        return data.get('rows') or []
    return data or []


def main():
    login = urllib.request.Request(
        API + '/auth/login',
        data=json.dumps({'tenantCode': '350600', 'username': 'admin',
                         'password': 'admin123'}).encode(),
        method='POST',
        headers={'Content-Type': 'application/json', 'X-Tenant-Id': '350600'})
    tok = json.loads(urllib.request.urlopen(login, timeout=40).read().decode())['data']['token']

    org = next((x for x in rows(call('/orgs?pageNum=1&pageSize=100', tok))
                if x['orgName'] == ORG), None)
    if not org:
        print('未找到 %s' % ORG)
        return 1
    oid = org['id']

    print('=' * 62)
    print('一期示范数据清单  ——  %s' % ORG)
    print('=' * 62)

    stats = []

    def add(label, items, note=''):
        stats.append((label, len(items), note))

    add('空间节点', rows(call('/spaces/tree?orgId=%s' % oid, tok)))
    add('房源', rows(call('/houses?pageNum=1&pageSize=200&orgId=%s' % oid, tok)))
    persons = rows(call('/persons?pageNum=1&pageSize=200&orgId=%s' % oid, tok))
    add('保障对象', persons)
    apps = [a for a in rows(call('/applications?pageNum=1&pageSize=200', tok))
            if a.get('orgId') == oid]
    add('申请单', apps,
        '通过 %d' % len([a for a in apps if a.get('applicationStatus') == 'APPROVED']))
    wait = rows(call('/allocation/waiting?pageNum=1&pageSize=200&securityType=PUBLIC', tok))
    add('轮候人员', wait)
    batches = [b for b in rows(call('/allocation/batches?pageNum=1&pageSize=100', tok))
               if b.get('orgId') == oid]
    add('配租批次', batches, '状态 ' + '/'.join(sorted({b.get('batchStatus') for b in batches})))
    contracts = [c for c in rows(call('/contracts?pageNum=1&pageSize=200', tok))
                 if c.get('orgId') == oid]
    add('合同', contracts,
        '履约 %d' % len([c for c in contracts if c.get('contractStatus') == 'EFFECTIVE']))
    bills = rows(call('/fin/bills?pageNum=1&pageSize=200&orgId=%s' % oid, tok))
    add('账单', bills)
    pubs = [p for p in rows(call('/publicities?pageNum=1&pageSize=100', tok))
            if p.get('orgId') == oid]
    add('公示', pubs)
    if pubs:
        w = rows(call('/publicities/%s/winners' % pubs[0]['id'], tok))
        add('中签名单', w, '来自最近公示')

    for label, n, note in stats:
        print('  %-10s %4d %s' % (label, n, ('  ' + note) if note else ''))

    print('-' * 62)
    if batches:
        b = batches[0]
        print('  批次：%s  %s' % (b.get('batchName'), b.get('batchStatus')))
    if contracts:
        c = contracts[0]
        print('  合同样例：%s  %s  承租人 %s'
              % (c.get('contractNo'), c.get('contractStatus'), c.get('lesseeName')))
    print('=' * 62)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
