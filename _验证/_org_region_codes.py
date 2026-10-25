# -*- coding: utf-8 -*-
"""组织标准地址：增加五级代码字段（省/市/区县/街道/社区）。

对应国家统计局五级区划：level1 省、2 市、3 区县、4 街道乡镇、5 社区/村。
当前区划库只到 4 级，第 5 级（社区）由前端下拉（可手填）自由录入，
故 community_code 允许为空。
"""
import io
import os
import pymysql

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
IAM = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'iam')

COLS = [
    ('province_code', 'varchar(20)'),
    ('city_code', 'varchar(20)'),
    ('district_code', 'varchar(20)'),
    ('street_code', 'varchar(20)'),
    ('community_code', 'varchar(20)'),
]

# ---------- 1) 数据库 ----------
c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                    password='5677@Mysql', database='bp_platform',
                    charset='utf8mb4', autocommit=True)
cur = c.cursor()
cur.execute('show columns from bp_iam_org')
have = {r[0] for r in cur.fetchall()}
for name, typ in COLS:
    if name in have:
        print('已存在:', name)
        continue
    cur.execute('alter table bp_iam_org add column %s %s null comment %s'
                % (name, typ, "'标准地址代码'"))
    print('已加列:', name)

# 用名称回填代码（按区划库匹配）
cur.execute('select id, province, city, district, street from bp_iam_org')
orgs = cur.fetchall()
n = 0
for oid, prov, city, dist, street in orgs:
    codes = []
    for name in (prov, city, dist, street):
        if not name:
            codes.append(None)
            continue
        cur.execute('select code from bp_sys_region where name=%s limit 1', (name,))
        row = cur.fetchone()
        codes.append(row[0] if row else None)
    if any(codes):
        cur.execute('''update bp_iam_org set province_code=%s, city_code=%s,
                       district_code=%s, street_code=%s where id=%s''',
                    (codes[0], codes[1], codes[2], codes[3], oid))
        n += 1
print('按名称回填代码:', n)
c.close()

# ---------- 2) 实体 ----------
P = os.path.join(IAM, 'entity', 'IamOrg.java')
s = io.open(P, encoding='utf-8').read()
if 'provinceCode' not in s:
    s = s.replace('''    private String province;''', '''    private String province;
    private String provinceCode;
    private String cityCode;
    private String districtCode;
    private String streetCode;
    private String communityCode;''')
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('IamOrg：已加代码字段')

# ---------- 3) Cmd ----------
P = os.path.join(IAM, 'dto', 'OrgCreateCmd.java')
s = io.open(P, encoding='utf-8').read()
if 'provinceCode' not in s:
    # 在 record 末尾补充字段：找到最后一个 ) 前插入
    i = s.rfind(')')
    j = s.rfind('{', 0, i)
    seg = s[j:i]
    need = ['String provinceCode', 'String cityCode', 'String districtCode',
            'String streetCode', 'String communityCode']
    add = ',\n        '.join(need)
    if seg.rstrip().endswith(','):
        s = s[:i] + '\n        ' + add + s[i:]
    else:
        s = s[:i] + ',\n        ' + add + '\n        ' + s[i:]
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('OrgCreateCmd：已加代码字段')

# ---------- 4) VO ----------
P = os.path.join(IAM, 'dto', 'OrgVO.java')
s = io.open(P, encoding='utf-8').read()
if 'provinceCode' not in s:
    s = s.replace('''        String province,''', '''        String province,
        String provinceCode,
        String cityCode,
        String districtCode,
        String streetCode,
        String communityCode,''')
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('OrgVO：已加代码字段')
