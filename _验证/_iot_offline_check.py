# -*- coding: utf-8 -*-
"""离线判定 Job 验证：把设备上次上报时间改到阈值外，等待 Job 置离线。"""
import json
import time
import urllib.request

import pymysql

BASE = 'http://192.168.31.11:8080'
DEV = 'LK00005771'

db = pymysql.connect(host='192.168.31.153', port=33306, user='root', password='5677@Mysql',
                     database='bp_platform', charset='utf8mb4', autocommit=True,
                     connect_timeout=20, read_timeout=120)
cur = db.cursor()
cur.execute('update bp_dev_device set online_status=1, last_report_time=now() - interval 10 minute '
            'where device_id=%s', (DEV,))
print('已把设备置为「在线但 10 分钟无心跳」:', DEV)
db.close()

for i in range(16):
    time.sleep(10)
    db = pymysql.connect(host='192.168.31.153', port=33306, user='root', password='5677@Mysql',
                         database='bp_platform', charset='utf8mb4', autocommit=True,
                         connect_timeout=20, read_timeout=120)
    cur = db.cursor()
    cur.execute('select online_status, offline_time from bp_dev_device where device_id=%s', (DEV,))
    row = cur.fetchone()
    cur.execute("select count(*) from bp_dev_event where event_id like 'AUTO-OFF-LK00005771%'")
    n = cur.fetchone()[0]
    db.close()
    print('第 %d 次检查：online_status=%s 自动离线事件=%d' % (i + 1, row[0], n))
    if row[0] == 0 and n > 0:
        print('离线判定生效')
        break
