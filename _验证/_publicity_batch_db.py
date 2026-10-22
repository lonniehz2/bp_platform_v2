# -*- coding: utf-8 -*-
"""补 DB 字段 + 让公示创建写入 batchId。"""
import io
import os

import pymysql

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# 1) 建列
conn = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                       password='5677@Mysql', database='bp_platform', charset='utf8mb4')
cur = conn.cursor()
cur.execute("show columns from bp_biz_publicity like 'batch_id'")
if not cur.fetchone():
    cur.execute('alter table bp_biz_publicity add column batch_id bigint null comment "关联配租批次"')
    conn.commit()
    print('已加列 bp_biz_publicity.batch_id')
else:
    print('列已存在')
conn.close()

# 2) create 写入 batchId
I = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp',
                 'biz', 'service', 'impl', 'PublicityServiceImpl.java')
s = io.open(I, encoding='utf-8').read()
if 'setBatchId' not in s:
    if 'e.setOrgId(cmd.orgId());' in s:
        s = s.replace('e.setOrgId(cmd.orgId());',
                      'e.setOrgId(cmd.orgId());\n'
                      '        e.setBatchId(cmd.batchId());   // 关联批次，用于公示中签名单', 1)
    else:
        # 兜底：找 setTitle 之类的创建处
        i = s.find('e.setPublicityNo(')
        j = s.find('\n', i) + 1
        s = s[:j] + '        e.setBatchId(cmd.batchId());\n' + s[j:]
    io.open(I, 'w', encoding='utf-8', newline='').write(s)
    print('PublicityServiceImpl：已写入 batchId')
else:
    print('batchId 已写入')
