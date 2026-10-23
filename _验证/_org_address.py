# -*- coding: utf-8 -*-
"""组织五级标准地址：省/地市/区县/街道/社区 + 详细地址。

按《人员账号-钥匙-设备关系说明》口径：
  标准地址 = 省 / 地市 / 区县 / 街道乡镇 / 社区村
  组织地址 = 标准地址 + 自定义详细地址（路牌、楼宇、房号）
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'iam')

FIELDS = [('province', 'String'), ('city', 'String'), ('district', 'String'),
          ('street', 'String'), ('community', 'String')]

# ---------- 实体 ----------
E = os.path.join(J, 'entity', 'IamOrg.java')
s = io.open(E, encoding='utf-8').read()
if 'private String province' not in s:
    add = ''
    for name, _ in FIELDS:
        add += '    /** 标准地址-{0} */\n    private String {0};\n\n'.format(name)
    i = s.find('    private BigDecimal longitude')
    s = s[:i] + add + s[i:]
    io.open(E, 'w', encoding='utf-8', newline='').write(s)
    print('IamOrg：五级地址字段已加')

# ---------- VO ----------
V = os.path.join(J, 'dto', 'OrgVO.java')
s = io.open(V, encoding='utf-8').read()
if 'String province' not in s:
    s = s.replace('        String address,',
                  '        String province, String city, String district,\n'
                  '        String street, String community,\n'
                  '        String address,', 1)
    io.open(V, 'w', encoding='utf-8', newline='').write(s)
    print('OrgVO：已加五级地址')

# ---------- CreateCmd ----------
C = os.path.join(J, 'dto', 'OrgCreateCmd.java')
s = io.open(C, encoding='utf-8').read()
if 'String province' not in s:
    s = s.replace('        String address,',
                  '        String province, String city, String district,\n'
                  '        String street, String community,\n'
                  '        String address,', 1)
    io.open(C, 'w', encoding='utf-8', newline='').write(s)
    print('OrgCreateCmd：已加五级地址')

# ---------- Service 映射 ----------
I = os.path.join(J, 'service', 'impl', 'OrgServiceImpl.java')
s = io.open(I, encoding='utf-8').read()
if 'setProvince' not in s:
    if 'e.setAddress(cmd.address());' in s:
        s = s.replace('e.setAddress(cmd.address());',
                      'e.setProvince(cmd.province());\n'
                      '        e.setCity(cmd.city());\n'
                      '        e.setDistrict(cmd.district());\n'
                      '        e.setStreet(cmd.street());\n'
                      '        e.setCommunity(cmd.community());\n'
                      '        e.setAddress(cmd.address());', 1)
        io.open(I, 'w', encoding='utf-8', newline='').write(s)
        print('OrgServiceImpl：创建时写入五级地址')

# ---------- VO 转换 ----------
n = 0
for cand in ('OrgServiceImpl.java', 'OrgVO.java'):
    p = os.path.join(J, 'service', 'impl', cand)
    if not os.path.exists(p):
        continue
    s = io.open(p, encoding='utf-8').read()
    if 'from(e)' in s and 'e.getProvince()' not in s:
        s = s.replace('e.getAddress()',
                      'e.getProvince(), e.getCity(), e.getDistrict(), e.getStreet(),\n'
                      '                e.getCommunity(), e.getAddress()', 1)
        io.open(p, 'w', encoding='utf-8', newline='').write(s)
        n += 1
print('VO 转换已更新 %d 处' % n)
print('完成')
