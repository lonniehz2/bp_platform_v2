# -*- coding: utf-8 -*-
"""回调网关压测：按指定 QPS 持续发送心跳回调，统计成功率与延迟。

用法：
  python _iot_load_test.py [qps] [seconds]
默认 50 QPS × 30 秒（1500 次）。心跳回调不新增业务行，适合压验签/幂等链路。
"""
import hashlib
import hmac
import json
import statistics
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor

BASE = 'http://192.168.31.11:8080'
APP_ID = 'bp-test-app'
SECRET = 'bp-test-secret'
PATH = '/api/callback/iot/heartbeat'

QPS = int(sys.argv[1]) if len(sys.argv) > 1 else 50
SECONDS = int(sys.argv[2]) if len(sys.argv) > 2 else 30
TOTAL = QPS * SECONDS

lat = []
codes = {}
lock = threading.Lock()


def sign(body, ts, nonce):
    canonical = ('POST\n' + PATH + '\n' + APP_ID + '\n' + ts + '\n' + nonce + '\n'
                 + hashlib.sha256(body.encode('utf-8')).hexdigest())
    return hmac.new(SECRET.encode('utf-8'), canonical.encode('utf-8'),
                    hashlib.sha256).hexdigest()


def one(_):
    body = json.dumps({'deviceId': 'LK00005771', 'battery': 80,
                       'reportTime': time.strftime('%Y-%m-%d %H:%M:%S')},
                      ensure_ascii=False, separators=(',', ':'))
    ts = str(int(time.time()))
    nonce = uuid.uuid4().hex
    headers = {'Content-Type': 'application/json', 'X-Iot-AppId': APP_ID,
               'X-Iot-Timestamp': ts, 'X-Iot-Nonce': nonce,
               'X-Iot-Signature': sign(body, ts, nonce)}
    t0 = time.time()
    try:
        req = urllib.request.Request(BASE + PATH, data=body.encode('utf-8'),
                                     headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=20) as r:
            code = json.loads(r.read().decode()).get('code', 'HTTP%d' % r.status)
    except urllib.error.HTTPError as e:
        code = 'HTTP%d' % e.code
    except Exception as e:
        code = 'ERR:' + type(e).__name__
    cost = (time.time() - t0) * 1000
    with lock:
        lat.append(cost)
        codes[code] = codes.get(code, 0) + 1


def main():
    print('压测：%d QPS × %d 秒 = %d 次，目标 %s' % (QPS, SECONDS, TOTAL, PATH))
    start = time.time()
    with ThreadPoolExecutor(max_workers=QPS) as pool:
        for i in range(TOTAL):
            pool.submit(one, i)
            # 均匀发送，避免瞬时并发把连接池打满
            target = start + (i + 1) / QPS
            sleep = target - time.time()
            if sleep > 0:
                time.sleep(sleep)
        pool.shutdown(wait=True)
    elapsed = time.time() - start
    ok = codes.get('SUCCESS', 0) + codes.get('0', 0)
    lat_sorted = sorted(lat)
    p50 = statistics.median(lat_sorted) if lat_sorted else 0
    p95 = lat_sorted[int(len(lat_sorted) * 0.95) - 1] if lat_sorted else 0
    print('耗时 %.1fs，实际 QPS %.1f' % (elapsed, len(lat) / elapsed))
    print('响应码分布：%s' % json.dumps(codes, ensure_ascii=False))
    print('成功 %d / %d（%.2f%%）' % (ok, len(lat), ok * 100.0 / max(1, len(lat))))
    print('延迟 ms：p50=%.0f  p95=%.0f  max=%.0f' % (p50, p95, max(lat_sorted or [0])))


if __name__ == '__main__':
    main()
