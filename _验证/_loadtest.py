# -*- coding: utf-8 -*-
"""压力测试：多场景并发压测（纯标准库，无需外部依赖）

用法：python _loadtest.py [并发数] [每场景秒数]
"""
import json
import statistics
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import Counter

BASE = 'http://192.168.31.11:8080'
TENANT = '350600'
CONCURRENCY = int(sys.argv[1]) if len(sys.argv) > 1 else 20
DURATION = int(sys.argv[2]) if len(sys.argv) > 2 else 10

TOKEN = None


def login():
    body = json.dumps({'tenantId': TENANT, 'username': 'admin',
                       'password': 'admin123'}).encode()
    r = urllib.request.Request(BASE + '/api/v1/auth/login', data=body, method='POST',
                               headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(r, timeout=30) as x:
        j = json.loads(x.read().decode())
    return j['data']['token']


def one_request(method, path, body=None):
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': TENANT}
    if TOKEN:
        h['Authorization'] = 'Bearer ' + TOKEN
    d = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=d, method=method, headers=h)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(r, timeout=30) as x:
            raw = x.read()
            ms = (time.perf_counter() - t0) * 1000
            code = None
            try:
                code = json.loads(raw.decode('utf-8', 'replace')).get('code')
            except Exception:
                pass
            return ms, 200, code
    except urllib.error.HTTPError as e:
        ms = (time.perf_counter() - t0) * 1000
        try:
            j = json.loads(e.read().decode('utf-8', 'replace'))
            return ms, e.code, j.get('code')
        except Exception:
            return ms, e.code, None
    except Exception as ex:
        ms = (time.perf_counter() - t0) * 1000
        return ms, -1, type(ex).__name__


def run_scenario(name, method, path, body=None, conc=None, dur=None):
    conc = conc or CONCURRENCY
    dur = dur or DURATION
    lat = []
    http_codes = Counter()
    biz_codes = Counter()
    lock = threading.Lock()
    stop_at = time.perf_counter() + dur
    barrier = threading.Barrier(conc)

    def worker():
        local_lat = []
        local_http = Counter()
        local_biz = Counter()
        try:
            barrier.wait(timeout=30)
        except Exception:
            pass
        while time.perf_counter() < stop_at:
            ms, hs, code = one_request(method, path, body)
            local_lat.append(ms)
            local_http[hs] += 1
            if code:
                local_biz[code] += 1
        with lock:
            lat.extend(local_lat)
            http_codes.update(local_http)
            biz_codes.update(local_biz)

    threads = [threading.Thread(target=worker, daemon=True) for _ in range(conc)]
    t_start = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=dur + 60)
    elapsed = time.perf_counter() - t_start

    if not lat:
        print('  %-40s 无数据' % name)
        return None
    lat.sort()
    total = len(lat)
    ok = http_codes.get(200, 0)
    p = lambda q: lat[min(int(total * q), total - 1)]  # noqa: E731
    res = {
        'name': name, 'conc': conc, 'elapsed': elapsed, 'total': total,
        'rps': total / elapsed if elapsed else 0,
        'ok': ok, 'err': total - ok,
        'err_rate': (total - ok) * 100.0 / total,
        'p50': p(0.50), 'p95': p(0.95), 'p99': p(0.99), 'max': lat[-1],
        'http': dict(http_codes), 'biz': dict(biz_codes),
    }
    print('  %-40s 并发%-3d 请求%-6d RPS%-7.1f p50%-6.1f p95%-6.1f p99%-6.1f 错误%.1f%%'
          % (name, conc, total, res['rps'], res['p50'], res['p95'], res['p99'],
             res['err_rate']))
    if res['err']:
        print('       错误分布: %s' % res['http'])
        print('       业务码: %s' % dict(list(res['biz'].items())[:5]))
    return res


print('=' * 96)
print(' 压力测试 · %d 并发 × %d 秒/场景' % (CONCURRENCY, DURATION))
print('=' * 96)

print('[warmup] 登录并预热 ...')
TOKEN = login()
for _ in range(5):
    one_request('GET', '/api/v1/rpt/metrics/current')
print('         预热完成')

results = []
print()
print('[1/6] 轻量读：组织分页')
results.append(run_scenario('GET /orgs（分页读）', 'GET',
                            '/api/v1/orgs?pageNum=1&pageSize=20'))

print('[2/6] 中等读：房屋分页')
results.append(run_scenario('GET /houses（分页读）', 'GET',
                            '/api/v1/houses?pageNum=1&pageSize=20'))

print('[3/6] 聚合读：实时指标（9 项聚合查询）')
results.append(run_scenario('GET /rpt/metrics/current（指标聚合）', 'GET',
                            '/api/v1/rpt/metrics/current'))

print('[4/6] 重聚合：大屏数据（8 组件 × 聚合）')
results.append(run_scenario('GET /rpt/screens/OVERVIEW/data（大屏）', 'GET',
                            '/api/v1/rpt/screens/OVERVIEW/data'))

print('[5/6] 报表查询：房源台账')
results.append(run_scenario('POST /rpt/reports/query（报表）', 'POST',
                            '/api/v1/rpt/reports/query',
                            {'reportCode': 'HOUSE_LEDGER', 'pageNum': 1, 'pageSize': 50}))

print('[6/6] 认证：登录（PBKDF2 12 万次迭代，天然慢）')
results.append(run_scenario('POST /auth/login（登录）', 'POST', '/api/v1/auth/login',
                            {'tenantId': TENANT, 'username': 'admin',
                             'password': 'admin123'}, conc=5, dur=max(5, DURATION // 2)))

print()
print('=' * 96)
print(' 汇总')
print('=' * 96)
print('%-38s %6s %9s %8s %8s %8s %8s' %
      ('场景', '并发', '总请求', 'RPS', 'p95(ms)', 'p99(ms)', '错误率'))
ok_results = [r for r in results if r]
for r in ok_results:
    print('%-38s %6d %9d %8.1f %8.1f %8.1f %7.1f%%' %
          (r['name'][:38], r['conc'], r['total'], r['rps'], r['p95'], r['p99'],
           r['err_rate']))

if ok_results:
    total_req = sum(r['total'] for r in ok_results)
    total_err = sum(r['err'] for r in ok_results)
    print()
    print('总计请求 %d，错误 %d（%.2f%%）' % (total_req, total_err,
                                            total_err * 100.0 / total_req))
    heaviest = max(ok_results, key=lambda r: r['p95'])
    slowest = min(ok_results, key=lambda r: r['rps'])
    print('最慢 p95：%s（%.1f ms）' % (heaviest['name'], heaviest['p95']))
    print('最低吞吐：%s（%.1f RPS）' % (slowest['name'], slowest['rps']))

out = r'D:\Work\业务平台开发\_验证\_loadtest_result.json'
with open(out, 'w', encoding='utf-8') as f:
    json.dump({'base': BASE, 'concurrency': CONCURRENCY, 'duration': DURATION,
               'results': ok_results}, f, ensure_ascii=False, indent=2)
print()
print('结果已保存：%s' % out)
