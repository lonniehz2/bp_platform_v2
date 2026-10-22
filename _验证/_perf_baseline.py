# -*- coding: utf-8 -*-
"""接口性能基线：测关键列表与详情接口耗时，给出 p50/p95 与慢接口清单。

用途：作为「性能稳定」的回归基线。每次改动后跑一次，超过阈值的接口需优化。
用法：python _perf_baseline.py [--rounds 5]
"""
import json
import statistics
import sys
import time
import urllib.error
import urllib.request

API = 'http://192.168.31.11:8080/api/v1'
ROUNDS = 5
for i, a in enumerate(sys.argv):
    if a == '--rounds' and i + 1 < len(sys.argv):
        ROUNDS = int(sys.argv[i + 1])

# (名称, 路径, 方法, 体)
CASES = [
    ('人员列表', '/persons?pageNum=1&pageSize=20', 'GET', None),
    ('房源列表', '/houses?pageNum=1&pageSize=20', 'GET', None),
    ('合同列表', '/contracts?pageNum=1&pageSize=20', 'GET', None),
    ('申请列表', '/applications?pageNum=1&pageSize=20', 'GET', None),
    ('轮候列表', '/allocation/waiting?pageNum=1&pageSize=20&securityType=PUBLIC', 'GET', None),
    ('账单列表', '/fin/bills?pageNum=1&pageSize=20', 'GET', None),
    ('配租批次', '/allocation/batches?pageNum=1&pageSize=20', 'GET', None),
    ('公示列表', '/publicities?pageNum=1&pageSize=20', 'GET', None),
    ('组织树', '/orgs?pageNum=1&pageSize=20', 'GET', None),
    ('空间树', '/spaces/tree?orgId=370988445033697280', 'GET', None),
    ('权限清单', '/rbac/permissions', 'GET', None),
    ('角色权限', '/rbac/roles', 'GET', None),
    ('报表模板', '/rpt/reports?pageNum=1&pageSize=20', 'GET', None),
    ('报表指标', '/rpt/metrics/current', 'GET', None),
    ('大屏列表', '/rpt/screens?pageNum=1&pageSize=20', 'GET', None),
]

SLOW_MS = 800


def call(path, method='GET', body=None, token=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=data, method=method)
    r.add_header('Content-Type', 'application/json')
    r.add_header('X-Tenant-Id', '350600')
    if token:
        r.add_header('Authorization', 'Bearer ' + token)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(r, timeout=60) as x:
            payload = json.loads(x.read().decode())
        return (time.perf_counter() - t0) * 1000, payload.get('code')
    except urllib.error.HTTPError as e:
        return (time.perf_counter() - t0) * 1000, 'HTTP%d' % e.code
    except Exception as e:
        return (time.perf_counter() - t0) * 1000, 'ERR:' + type(e).__name__


def main():
    login = urllib.request.Request(
        API + '/auth/login',
        data=json.dumps({'tenantCode': '350600', 'username': 'admin',
                         'password': 'admin123'}).encode(),
        method='POST',
        headers={'Content-Type': 'application/json', 'X-Tenant-Id': '350600'})
    tok = json.loads(urllib.request.urlopen(login, timeout=40).read().decode())['data']['token']

    print('%-10s %8s %8s %8s  %s' % ('接口', 'p50', 'p95', 'max', '状态'))
    print('-' * 62)
    slow = []
    all_ms = []
    for name, path, method, body in CASES:
        times, code = [], None
        for _ in range(ROUNDS):
            ms, code = call(path, method, body, tok)
            times.append(ms)
        times.sort()
        p50 = statistics.median(times)
        p95 = times[max(0, int(len(times) * 0.95) - 1)]
        mx = times[-1]
        all_ms.extend(times)
        flag = 'OK' if p95 < SLOW_MS else 'SLOW'
        if p95 >= SLOW_MS:
            slow.append((name, p95, mx, code))
        print('%-10s %7.0fms %7.0fms %7.0fms  %s %s'
              % (name, p50, p95, mx, flag, '' if code == 'BP00000' else code))

    print('-' * 62)
    all_ms.sort()
    print('总体：p50 %.0fms  p95 %.0fms  max %.0fms  共 %d 次请求'
          % (statistics.median(all_ms), all_ms[max(0, int(len(all_ms) * 0.95) - 1)],
             all_ms[-1], len(all_ms)))
    if slow:
        print('\n慢接口（p95 ≥ %dms）：' % SLOW_MS)
        for name, p95, mx, code in slow:
            print('  %-10s p95 %.0fms  max %.0fms  %s' % (name, p95, mx, code))
    else:
        print('\n无慢接口（阈值 %dms）' % SLOW_MS)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
