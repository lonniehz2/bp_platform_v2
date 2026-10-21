# -*- coding: utf-8 -*-
# ===== 统一连接配置（由 _验证/verify.py 注入环境变量）=====
import os as _os
HOST  = _os.environ.get('BP_DB_HOST', '192.168.31.153')
PORT  = int(_os.environ.get('BP_DB_PORT', '33306'))
USER  = _os.environ.get('BP_DB_USER', 'root')
PWD   = _os.environ.get('BP_DB_PWD',  '5677@Mysql')
DB    = _os.environ.get('BP_DB_NAME', 'bp_platform')
BASE  = _os.environ.get('BP_PROJ_DIR', r'D:\Work\业务平台开发')
# =========================================================
"""冒烟测试：真实读写 + 唯一约束 + 分区路由"""
import pymysql

c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                    password='5677@Mysql', database='bp_platform', charset='utf8mb4')
cur = c.cursor()

print('--- 1) 基础写入（显式雪花 ID，符合设计：应用层生成主键）---')
TID = 1000000000000000001
OID = 1000000000000000002
cur.execute("""INSERT INTO bp_iam_tenant(id,tenant_code,tenant_name,tenant_type,isolation_mode,
               status,create_by,create_time,update_by,update_time)
               VALUES(%s,'TEST001','冒烟测试租户','ORG','ROW','ENABLED','sys',NOW(3),'sys',NOW(3))""", (TID,))
print('  租户插入成功 id=%s' % TID)

cur.execute("""INSERT INTO bp_iam_org(id,tenant_id,org_code,org_name,org_type,create_time,update_time)
               VALUES(%s,'TEST001','ORG001','测试小区','COMMUNITY',NOW(3),NOW(3))""", (OID,))
print('  组织插入成功 id=%s' % OID)

print('--- 2) 唯一约束验证（重复 org_code 应被拒）---')
try:
    cur.execute("""INSERT INTO bp_iam_org(id,tenant_id,org_code,org_name,org_type,create_time,update_time)
                   VALUES(%s,'TEST001','ORG001','重复组织','COMMUNITY',NOW(3),NOW(3))""", (OID + 1,))
    print('  !! 唯一约束未生效（异常情况）')
except Exception as e:
    print('  [OK] 唯一约束生效 -> %s' % str(e)[:90])

print('--- 3) 分区路由验证 ---')
cur.execute("""INSERT INTO bp_dev_access_record(id,tenant_id,event_id,open_type,open_time,source,create_time)
               VALUES(%s,'TEST001','EV_TEST_1','1049','2026-10-16 10:00:00','CALLBACK',NOW(3))""", (OID + 2,))
print('  分区表插入成功')
cur.execute("SELECT COUNT(*) FROM bp_dev_access_record PARTITION(p202610)")
print('  落在 p202610 分区行数: %s' % cur.fetchone()[0])
cur.execute("SELECT COUNT(*) FROM bp_dev_access_record PARTITION(pmax)")
print('  落在 pmax 分区行数（应为 0）: %s' % cur.fetchone()[0])

cur.execute("""INSERT INTO bp_dev_access_record(id,tenant_id,event_id,open_type,open_time,source,create_time)
               VALUES(%s,'TEST001','EV_TEST_2','1005','2026-11-16 10:00:00','CALLBACK',NOW(3))""", (OID + 3,))
cur.execute("SELECT COUNT(*) FROM bp_dev_access_record PARTITION(p202611)")
print('  跨月记录落在 p202611 行数: %s' % cur.fetchone()[0])

print('--- 4) 关联查询验证 ---')
cur.execute("""SELECT o.org_name FROM bp_iam_org o
               WHERE o.tenant_id='TEST001' AND o.org_code='ORG001'""")
print('  查询结果: %s' % cur.fetchone())

print('--- 5) 幂等唯一索引验证（同 event_id 重复插入应被拒）---')
try:
    cur.execute("""INSERT INTO bp_dev_access_record(id,tenant_id,event_id,open_type,open_time,source,create_time)
                   VALUES(%s,'TEST001','EV_TEST_1','1049','2026-10-16 10:00:00','CALLBACK',NOW(3))""", (OID + 4,))
    print('  !! 幂等索引未生效（异常情况）')
except Exception as e:
    print('  [OK] 幂等唯一索引生效 -> %s' % str(e)[:90])

c.rollback()
c.close()
print('\n已回滚，未留测试数据')
print('DONE')
