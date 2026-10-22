# -*- coding: utf-8 -*-
"""性能优化第一批：
1) 门禁记录补 (tenant_id, org_id, open_time) 与 (tenant_id, is_abnormal, open_time) 索引
2) MetricServiceImpl.currentAll 复用中间结果，避免重复查询（占用率重复查总数/已租）
"""
import io
import os

import pymysql

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# ---------- 1) 索引 ----------
conn = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                       password='5677@Mysql', database='bp_platform', charset='utf8mb4')
cur = conn.cursor()

cur.execute('show index from bp_dev_access_record')
existing = {r[2] for r in cur.fetchall()}

IDX = [
    ('idx_tenant_org_time', 'alter table bp_dev_access_record '
                            'add index idx_tenant_org_time (tenant_id, org_id, open_time)'),
    ('idx_tenant_abnormal_time', 'alter table bp_dev_access_record '
                                 'add index idx_tenant_abnormal_time '
                                 '(tenant_id, is_abnormal, open_time)'),
]
for name, ddl in IDX:
    if name in existing:
        print('%s 已存在' % name)
        continue
    try:
        cur.execute(ddl)
        conn.commit()
        print('已创建索引 %s' % name)
    except Exception as ex:
        print('创建 %s 失败：%s' % (name, ex))

cur.execute('show index from bp_dev_access_record')
print('现有索引：', sorted({r[2] for r in cur.fetchall()}))
conn.close()

# ---------- 2) currentAll 复用结果 ----------
P = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp',
                 'rpt', 'service', 'impl', 'MetricServiceImpl.java')
s = io.open(P, encoding='utf-8').read()

old = '''    public Map<String, Object> currentAll(Long orgId) {
        Map<String, Object> m = new LinkedHashMap<>();
        for (String code : List.of("HOUSE_TOTAL", "HOUSE_OCCUPIED", "HOUSE_VACANT",
                "OCCUPANCY_RATE", "BILL_UNPAID_COUNT", "BILL_UNPAID_AMOUNT",
                "PAYMENT_TOTAL_AMOUNT", "ACCESS_TODAY_COUNT", "ACCESS_ABNORMAL_COUNT")) {
            m.put(code, current(code, orgId));
        }'''
new = '''    public Map<String, Object> currentAll(Long orgId) {
        Map<String, Object> m = new LinkedHashMap<>();
        // 房源总量/已租/空置各查一次，占用率复用前两者的结果（避免重复查询）
        for (String code : List.of("HOUSE_TOTAL", "HOUSE_OCCUPIED", "HOUSE_VACANT")) {
            m.put(code, current(code, orgId));
        }
        double total = ((Number) m.get("HOUSE_TOTAL")).doubleValue();
        double occupied = ((Number) m.get("HOUSE_OCCUPIED")).doubleValue();
        m.put("OCCUPANCY_RATE",
                total == 0 ? 0.0 : Math.round(occupied * 10000.0 / total) / 100.0);
        for (String code : List.of("BILL_UNPAID_COUNT", "BILL_UNPAID_AMOUNT",
                "PAYMENT_TOTAL_AMOUNT", "ACCESS_TODAY_COUNT", "ACCESS_ABNORMAL_COUNT")) {
            m.put(code, current(code, orgId));
        }'''

if old in s:
    s = s.replace(old, new, 1)
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('MetricServiceImpl.currentAll 已优化（复用中间结果）')
else:
    print('未匹配 currentAll，请人工核对')
