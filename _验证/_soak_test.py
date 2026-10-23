# -*- coding: utf-8 -*-
"""长稳测试：持续打接口，观察内存、GC、连接池与延迟趋势。

用法：
  python _soak_test.py                 # 默认 20 分钟
  python _soak_test.py --minutes 5     # 快速验证
结果：每 5 分钟一段的 p50/p95、内存首尾对比、GC 次数增量、连接池峰值、错误数。
"""
import json
import statistics
import sys
import time
import urllib.error
import urllib.request

API = 'http://192.168.31.11:8080/api/v1'
BASE = 'http://192.168.31.11:8080'

MINUTES = 20
for i, a in enumerate(sys.argv):
    if a == '--minutes' and i + 1 < len(sys.argv):
        MINUTES = int(sys.argv[i + 1])

PATHS = [
    '/persons?pageNum=1&pageSize=20',
    '/houses?pageNum=1&pageSize=20',
    '/contracts?pageNum=1&pageSize=20',
    '/fin/bills?pageNum=1&pageSize=20',
    '/workorders?pageNum=1&pageSize=20',
    '/houses/beds?roomSpaceId=371689465527787520',
    '/fin/meter-readings?pageNum=1&pageSize=20',
]


def login():
    r = urllib.request.Request(
        API + '/auth/login',
        data=json.dumps({'tenantCode': '350600', 'username': 'admin',
                         'password': 'admin123'}).encode(),
        method='POST', headers={'Content-Type': 'application/json',
                                'X-Tenant-Id': '350600'})
    return json.loads(urllib.request.urlopen(r, timeout=30).read().decode())['data']['token']


def metric(path):
    try:
        with urllib.request.urlopen(BASE + path, timeout=10) as r:
            body = json.loads(r.read().decode())
        ms = {m['statistic']: m['value'] for m in body.get('measurements', [])}
        return ms
    except Exception:
        return {}


def call(path, tok):
    r = urllib.request.Request(API + path, headers={
        'Authorization': 'Bearer ' + tok, 'X-Tenant-Id': '350600'})
    t0 = time.time()
    try:
        with urllib.request.urlopen(r, timeout=30) as x:
            x.read()
        return (time.time() - t0) * 1000, True
    except Exception:
        return (time.time() - t0) * 1000, False


def main():
    tok = login()
    end = time.time() + MINUTES * 60
    samples = []        # (elapsed_sec, ms, ok)
    mem = []            # (elapsed_sec, bytes)
    gc = []             # (elapsed_sec, count)
    pool = []           # (elapsed_sec, active)
    errors = 0
    idx = 0
    t0 = time.time()
    last_sample = 0
    print('开始长稳测试：%d 分钟' % MINUTES)
    while time.time() < end:
        path = PATHS[idx % len(PATHS)]
        idx += 1
        ms, ok = call(path, tok)
        samples.append((time.time() - t0, ms, ok))
        if not ok:
            errors += 1
        el = time.time() - t0
        if el - last_sample >= 30:
            last_sample = el
            m = metric('/actuator/metrics/jvm.memory.used').get('VALUE')
            g = metric('/actuator/metrics/jvm.gc.pause').get('COUNT')
            p = metric('/actuator/metrics/hikaricp.connections.active').get('VALUE')
            if m is not None:
                mem.append((el, m))
            if g is not None:
                gc.append((el, g))
            if p is not None:
                pool.append((el, p))
            print('  %5.0fs  请求 %d  错误 %d  内存 %.0fMB  GC %s  连接 %s'
                  % (el, len(samples), errors, (m or 0) / 1048576,
                     int(g) if g is not None else '-', int(p) if p is not None else '-'))
        time.sleep(0.05)

    # ---------- 汇总 ----------
    print('\n===== 长稳结果 =====')
    print('总请求 %d，错误 %d（%.2f%%）'
          % (len(samples), errors, errors * 100.0 / max(len(samples), 1)))
    bucket = 300
    buckets = {}
    for el, ms, ok in samples:
        b = int(el // bucket)
        buckets.setdefault(b, []).append(ms)
    print('%-10s %8s %8s %8s' % ('时间段', 'p50', 'p95', '样本'))
    for b in sorted(buckets):
        v = buckets[b]
        p95 = sorted(v)[int(len(v) * 0.95) - 1] if len(v) > 1 else v[0]
        print('%3d-%3d 分 %7.0fms %7.0fms %8d'
              % (b * 5, (b + 1) * 5, statistics.median(v), p95, len(v)))
    if mem:
        first, last = mem[0][1], mem[-1][1]
        print('内存：首 %.0fMB → 末 %.0fMB（%+.1f%%）'
              % (first / 1048576, last / 1048576,
                 (last - first) * 100.0 / max(first, 1)))
    if gc and len(gc) > 1:
        print('GC 次数：%d → %d（+%d）' % (int(gc[0][1]), int(gc[-1][1]),
                                          int(gc[-1][1] - gc[0][1])))
    if pool:
        print('连接池峰值：%d' % int(max(x[1] for x in pool)))

    # 判定
    issues = []
    if errors:
        issues.append('存在错误请求')
    if len(buckets) >= 2:
        first_b = statistics.median(buckets[min(buckets)])
        last_b = statistics.median(buckets[max(buckets)])
        if first_b > 0 and last_b > first_b * 1.5:
            issues.append('延迟劣化超过 50%')
    # 内存判定：正常 JVM 是锯齿（涨到阈值 GC 回落）。
    # 真正的泄漏特征是「每次 GC 后的谷值」持续抬高，而不是峰值高。
    if mem:
        mx = metric('/actuator/metrics/jvm.memory.max').get('VALUE') or 0
        thirds = max(1, len(mem) // 3)
        first_vals = [x[1] for x in mem[:thirds]]
        last_vals = [x[1] for x in mem[-thirds:]]
        low_first, low_last = min(first_vals), min(last_vals)
        peak = max(x[1] for x in mem)
        print('内存判断：峰值 %.0fMB / 上限 %.0fMB；GC 后谷值 前段 %.0fMB → 后段 %.0fMB'
              % (peak / 1048576, mx / 1048576 if mx else 0,
                 low_first / 1048576, low_last / 1048576))
        if mx and peak > mx * 0.9:
            issues.append('堆使用接近上限（%.0f/%.0fMB）'
                          % (peak / 1048576, mx / 1048576))
        elif low_first > 0 and low_last > low_first * 1.5:
            issues.append('GC 后谷值抬升 %.0f%%（疑似泄漏）'
                          % ((low_last - low_first) * 100.0 / low_first))
    print('\n结论：%s' % ('稳定 ✔' if not issues else '需关注：' + '；'.join(issues)))
    return 0 if not issues else 1


if __name__ == '__main__':
    raise SystemExit(main())
