# -*- coding: utf-8 -*-
"""导出 org/space/person 三个创建 DTO 的字段 + 枚举值 + 生成合法身份证"""
import io
import os
import re

JAVA = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'


def dump_record(path):
    s = io.open(path, encoding='utf-8').read()
    m = re.search(r'record\s+(\w+)\s*\((.*?)\)\s*\{', s, re.S)
    if not m:
        return None
    body = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.S)
    out = []
    for ln in body.split('\n'):
        t = ln.strip().rstrip(',')
        if not t or t.startswith('//'):
            continue
        out.append(t)
    return m.group(1), out


for rel in ('iam/dto/OrgCreateCmd.java', 'asset/dto/SpaceCreateCmd.java',
            'person/dto/PersonCreateCmd.java'):
    p = os.path.join(JAVA, rel.replace('/', os.sep))
    if not os.path.exists(p):
        print('!! 未找到 %s' % rel)
        continue
    r = dump_record(p)
    print('=== %s ===' % rel)
    for x in r[1]:
        print('   ' + x[:120])
    print()

# 枚举值
for rel, name in (('iam/constant/OrgType.java', 'OrgType'),
                  ('asset/constant/SpaceType.java', 'SpaceType'),
                  ('person/constant/PersonType.java', 'PersonType')):
    p = os.path.join(JAVA, rel.replace('/', os.sep))
    if not os.path.exists(p):
        print('□ %s 未找到' % name)
        continue
    s = io.open(p, encoding='utf-8').read()
    vals = re.findall(r'^\s{4}([A-Z][A-Z_0-9]*)\s*[\(,]', s, re.M)
    print('%s: %s' % (name, ', '.join(vals)))

# 生成合法身份证（GB 11643 校验位）
def make_id(area='350600', birth='19900101', seq=1):
    body = '%s%s%03d' % (area, birth, seq)
    w = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    codes = '10X98765432'
    total = sum(int(body[i]) * w[i] for i in range(17))
    return body + codes[total % 11]


print()
print('合法身份证样例：')
for i in range(1, 6):
    print('   ' + make_id(seq=i))
