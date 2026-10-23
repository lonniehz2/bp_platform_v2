# -*- coding: utf-8 -*-
"""压力型性能测试：用较大分页、模糊查询、时间范围统计等重负载场景，
补充 _perf_baseline.py（基线只测轻量请求）。

输出：每个接口的 p50/p95/max，超过阈值标红。
"""
import json
import statistics
import time
import urllib.error
import urllib.request

API = 'http://192.168.31.11:8080/api/v1'
THRESHOLD = 800

CASES = [
    ('人员-大分页', '/persons?pageNum=1&pageSize=100'),
    ('人员-模糊查询', '/persons?pageNum=1&pageSize=50&keyword=%E5%BC%A0'),
    ('房源-大分页', '/houses?pageNum=1&pageSize=100'),
    ('房源-业态筛选', '/houses?pageNum=1&pageSize=100&houseType=PUBLIC_RENTAL'),
    ('合同-大分页', '/contracts?pageNum=1&pageSize=100'),
    ('账单-状态筛选', '/fin/bills?pageNum=1&pageSize=100&billStatus=UNPAID'),
    ('收款-大分页', '/fin/payments?pageNum=1&pageSize=100'),
    ('工单-大分页', '/workorders?pageNum=1&pageSize=100'),
    ('空间树', '/spaces/tree?orgId=371689292805836800'),
    ('报表模板', '/rpt/reports?pageNum=1&pageSize=50'),
    ('导出任务', '/rpt/exports?pageNum=1&pageSize=50'),
    ('门禁-大分页', '/access-records?pageNum=1&pageSize=100&orgId=371689292805836800'),
    ('待办汇总', '/todos/overview'),
    ('组织列表', '/orgs?pageNum=1&pageSize=100'),
    ('权限列表', '/rbac/permissions'),
]


def login():
    r = urllib.request.Request(
        API + '/auth/login',
        data=json.dumps({'tenantCode': '350600', 'username': 'admin',
                         'password': 'admin123'}).encode(),
        method='POST', headers={'Content-Type': 'application/json',
                                'X-Tenant-Id': '350600'})
    return json.loads(urllib.request.urlopen(r, timeout=30).read().decode())['data']['token']


def timed(path, tok):
    r = urllib.request.Request(API + path, headers={
        'Authorization': 'Bearer ' + tok, 'X-Tenant-Id': '350600'})
    t0 = time.time()
    code = 200
    try:
        with urllib.request.urlopen(r, timeout=60) as x:
            x.read()
    except urllib.error.HTTPError as e:
        code = e.code
    return (time.time() - t0) * 1000, code


def main():
    tok = login()
    print('%-14s %8s %8s %8s %6s' % ('场景', 'p50', 'p95', 'max', '状态'))
    print('-' * 52)
    slow = []
    for name, path in CASES:
        samples = []
        code = 200
        for _ in range(5):
            ms, code = timed(path, tok)
            samples.append(ms)
            time.sleep(0.05)
        p50 = statistics.median(samples)
        p95 = sorted(samples)[int(len(samples) * 0.95) - 1]
        mx = max(samples)
        flag = 'OK'
        if code >= 400:
            flag = 'HTTP%d' % code
        elif p95 > THRESHOLD:
            flag = 'SLOW'
            slow.append((name, p95))
        print('%-14s %7.0fms %7.0fms %7.0fms %6s' % (name, p50, p95, mx, flag))
    print('-' * 52)
    if slow:
        print('慢接口 %d 个（阈值 %dms）：%s'
              % (len(slow), THRESHOLD, '、'.join(n for n, _ in slow)))
    else:
        print('无慢接口（阈值 %dms）' % THRESHOLD)
    return 0 if not slow else 1


if __name__ == '__main__':
    raise SystemExit(main())
