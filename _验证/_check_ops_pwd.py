# -*- coding: utf-8 -*-
import base64
import hashlib
import pymysql

c = pymysql.connect(host='192.168.31.153', port=33306, user='root', password='5677@Mysql',
                    database='bp_platform', charset='utf8mb4', autocommit=True,
                    connect_timeout=20, read_timeout=60)
cur = c.cursor()
cur.execute("select password_hash, must_change_password, fail_count, locked_until "
            "from bp_iam_platform_operator where username='opsadmin'")
h, must, fail, locked = cur.fetchone()
parts = h.split('$')
print('parts', len(parts), 'must', must, 'fail', fail, 'locked', locked)
for pwd in ('Ops@123456', 'Ops@12345678'):
    dk = hashlib.pbkdf2_hmac('sha256', pwd.encode(), base64.b64decode(parts[2]),
                             int(parts[1]), dklen=32)
    print(pwd, dk == base64.b64decode(parts[3]))
c.close()
