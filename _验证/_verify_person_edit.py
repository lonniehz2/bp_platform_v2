# -*- coding: utf-8 -*-
"""实测：人员编辑 / 改状态 / 保障档案编辑与中文枚举"""
import json
import time
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
D = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json', encoding='utf-8'))
ORG = D.get('demoOrgId') or D.get('orgId')
TOK = None


def call(m, p, b=None):
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': '350600'}
    if TOK:
        h['Authorization'] = 'Bearer ' + TOK
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE + p, data=d, method=m, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=60) as x:
            return x.status, json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {'code': 'HTTP_%d' % e.code}
    except Exception as e:
        return -1, {'code': type(e).__name__}


def chk(name, res, expect=('BP00000',)):
    st, r = res
    code = r.get('code') or ('HTTP_%s' % st)
    ok = code in expect
    print('  %s %-28s %-10s %s' % ('✓' if ok else '✗', name, code,
                                  '' if ok else str(r.get('message'))[:48]))
    return (r.get('data') if ok else None), ok


TOK = call('POST', '/api/v1/auth/login',
           {'tenantId': '350600', 'username': 'admin', 'password': 'admin123'}
           )[1].get('data', {}).get('token')

print('=' * 68)
print(' ① 人员编辑（新增接口 PUT /persons/{id}）')
ps = call('GET', '/api/v1/persons?pageNum=1&pageSize=3')
rows = (ps[1].get('data') or {}).get('rows') or []
pid = rows[0]['id'] if rows else None
print('  选中人员：%s（%s）' % (rows[0].get('personName') if rows else '-', pid))

if pid:
    d, ok = chk('修改姓名/手机/学历', call('PUT', '/api/v1/persons/%s' % pid, {
        'personName': '改名测试' + str(int(time.time()))[-3:],
        'phone': '13800001234', 'education': '本科',
        'employer': '测试单位', 'remark': '实测修改'}))
    if ok:
        print('     返回姓名：%s 手机：%s 学历：%s'
              % (d.get('personName'), d.get('phone'), d.get('education')))
    d2, ok2 = chk('改状态为黑名单', call('POST',
        '/api/v1/persons/%s/status' % pid, {'status': 'BLACKLIST'}))
    if ok2:
        print('     返回状态：%s' % d2.get('personStatus'))
    chk('改回正常', call('POST', '/api/v1/persons/%s/status' % pid,
                       {'status': 'NORMAL'}))

print('\n' + '=' * 68)
print(' ② 保障档案编辑（POST 按 personId 覆盖）')
gs = call('GET', '/api/v1/guarantee-profiles?pageNum=1&pageSize=3')
grows = (gs[1].get('data') or {}).get('rows') or []
if grows:
    g = grows[0]
    print('  选档案：人员 %s 现收入档位=%s 现状态=%s'
          % (g.get('personId'), g.get('incomeLevel'), g.get('profileStatus')))
    d, ok = chk('编辑保障档案', call('POST', '/api/v1/guarantee-profiles', {
        'personId': g.get('personId'), 'securityType': 'PUBLIC',
        'familySize': 3, 'familyType': 'COUPLE',
        'monthlyIncome': 5000, 'assetDeclare': 2,
        'hasHouse': 0, 'hasVehicle': 1}))
    if ok:
        print('     更新后家庭人口=%s 月收入=%s' % (d.get('familySize'),
                                                d.get('monthlyIncome')))
    d2, ok2 = chk('收入重算', call('POST',
        '/api/v1/guarantee-profiles/person/%s/recalc-income' % g.get('personId'),
        {'lowLine': 1200, 'lowIncomeLine': 2400, 'middleLowLine': 4000}))
    if ok2:
        print('     重算后档位：%s' % (d2.get('incomeLevelAfter') or d2))

print('\n' + '=' * 68)
print(' ③ 枚举中文覆盖（前端字典校验）')
import io
import re
e = io.open(r'D:\Work\业务平台开发\frontend\src\constants\enums.js',
            encoding='utf-8').read()
for code in ('LOW', 'LOW_INCOME', 'MIDDLE_LOW', 'NORMAL', 'BLACKLIST',
             'CANCELLED', 'ACTIVE', 'EXITED', 'SINGLE', 'MARRIED', 'URBAN',
             'COUPLE', 'STAFF', 'ALL'):
    hit = re.search(r"^\s*'?%s'?\s*:\s*'([^']+)'" % code, e, re.M)
    print('  %s %-14s → %s' % ('✓' if hit else '✗', code,
                               hit.group(1) if hit else '缺失'))
