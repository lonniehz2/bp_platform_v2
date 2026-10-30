# -*- coding: utf-8 -*-
import base64
import hashlib
import os
import pymysql

PWD = 'Ops@123456'
salt = os.urandom(16)
dk = hashlib.pbkdf2_hmac('sha256', PWD.encode(), salt, 120000, dklen=32)
h = 'pbkdf2$120000$%s$%s' % (base64.b64encode(salt).decode(),
                             base64.b64encode(dk).decode())
print('format parts', len(h.split('$')))
c = pymysql.connect(host='192.168.31.153', port=33306, user='root', password='5677@Mysql',
                    database='bp_platform', charset='utf8mb4', autocommit=True,
                    connect_timeout=20, read_timeout=60)
cur = c.cursor()
cur.execute("""update bp_iam_platform_operator
    set password_hash=%s, must_change_password=1, fail_count=0,
        locked_until=null, status='ENABLED'
    where username='opsadmin'""", (h,))
print('reset', cur.rowcount)
cur.execute("select password_hash from bp_iam_platform_operator where username='opsadmin'")
print('stored parts', len(cur.fetchone()[0].split('$')))
c.close()
