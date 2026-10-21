# -*- coding: utf-8 -*-
"""建补贴标准→发放；登记催缴（正确字段）；抓 scan 真实异常"""
import io
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
TENANT = '350600'
TOK = None
D = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json', encoding='utf-8'))
ORG = D['orgId']


def call(m, p, b=None):
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': TENANT}
    if TOK:
        h['Authorization'] = 'Bearer ' + TOK
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE + p, data=d, method=m, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=90) as x:
            return json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {'code': 'HTTP_%d' % e.code}
    except Exception as e:
        return {'code': type(e).__name__, 'message': str(e)}


TOK = call('POST', '/api/v1/auth/login',
           {'tenantId': TENANT, 'username': 'admin', 'password': 'admin123'}
           ).get('data', {}).get('token')

# ---------- 1) 补贴标准 ----------
print('— 补贴标准 —')
sfx = str(int(time.time()))[-4:]
r = call('POST', '/api/v1/fin/subsidies/standards', {
    'standardCode': 'SUB' + sfx, 'standardName': '公租房租金补贴',
    'securityType': 'PUBLIC', 'orgId': ORG, 'subsidyMode': 'BY_AREA',
    'subsidyValue': 3.0, 'maxAmount': 500,
    'effectiveStart': '2026-01-01', 'effectiveEnd': '2026-12-31'})
print('  %s 建标准 → %s %s' % ('✓' if r.get('code') == 'BP00000' else '✗',
                              r.get('code'), str(r.get('message'))[:60]))

print('— 补贴发放 —')
r = call('POST', '/api/v1/fin/subsidies/records/batch', {
    'subsidyPeriod': '2026-10', 'orgId': ORG, 'payMode': 'OFFSET', 'dryRun': False})
print('  %s 发放 → %s' % ('✓' if r.get('code') == 'BP00000' else '✗',
                         str(r.get('data') or r.get('message'))[:110]))
subs = call('GET', '/api/v1/fin/subsidies/records?pageNum=1&pageSize=5')
rows = (subs.get('data') or {}).get('rows') or []
print('  补贴记录 %d 条' % len(rows))
for x in rows[:3]:
    print('    %s 人员%s 金额%s 状态%s' % (x.get('recordNo'), x.get('personId'),
                                        x.get('subsidyAmount'), x.get('recordStatus')))

# ---------- 2) 登记催缴（正确字段 dunningType）----------
print('\n— 催缴登记 —')
bills = call('GET', '/api/v1/fin/bills?pageNum=1&pageSize=3').get('data', {}).get('rows') or []
if bills:
    b0 = bills[0]
    r = call('POST', '/api/v1/fin/dunnings', {
        'billId': b0['id'], 'personId': b0.get('personId'),
        'dunningType': 'SMS', 'dunningContent': '请尽快缴纳本期租金',
        'operatorId': 1})
    print('  %s 登记催缴 → %s %s' % ('✓' if r.get('code') == 'BP00000' else '✗',
                                    r.get('code'), str(r.get('message'))[:60]))
    dn = call('GET', '/api/v1/fin/dunnings?pageNum=1&pageSize=5')
    print('  催缴记录 %s 条' % (dn.get('data') or {}).get('total'))

# ---------- 3) scan 真实异常 ----------
print('\n— 扫描催缴（抓异常）—')
r = call('POST', '/api/v1/fin/dunnings/scan')
print('  结果：%s %s' % (r.get('code'), str(r.get('message'))[:80]))
if r.get('code') != 'BP00000':
    p = subprocess.run(
        [sys.executable, 'vm.py',
         "tail -80 /var/log/bp-platform/app.log | grep -iE 'Caused by|Exception|Error' "
         "| tail -4"],
        capture_output=True, text=True, encoding='utf-8', errors='replace',
        cwd=r'D:\Work\业务平台开发\_验证')
    print('  日志：')
    for ln in (p.stdout or '').split('\n'):
        if ln.strip():
            print('    ' + ln.strip()[:150])

# ---------- 4) 修正前端催缴字段 ----------
P = r'D:\Work\业务平台开发\frontend\src\views\Arrears.vue'
s = io.open(P, encoding='utf-8').read()
if 'dunningType' not in s:
    s = s.replace("df = reactive({ billId: null, personId: null, actionType: 'SMS', remark: '' })",
                  "df = reactive({ billId: null, personId: null, dunningType: 'SMS',\n"
                  "  dunningContent: '', operatorId: 1 })")
    s = s.replace("v-model=\"df.actionType\"", "v-model=\"df.dunningType\"")
    s = s.replace('''            <el-option label="短信" value="SMS" />
            <el-option label="电话" value="CALL" />
            <el-option label="上门" value="VISIT" />
            <el-option label="律师函" value="LETTER" />''',
                  '''            <el-option label="短信" value="SMS" />
            <el-option label="微信" value="WECHAT" />
            <el-option label="电话" value="PHONE" />
            <el-option label="上门" value="VISIT" />
            <el-option label="书面通知" value="NOTICE" />
            <el-option label="平台推送" value="PLATFORM" />''')
    s = s.replace('''        <el-form-item label="备注">
          <el-input v-model="df.remark" type="textarea" :rows="2" /></el-form-item>''',
                  '''        <el-form-item label="催缴内容">
          <el-input v-model="df.dunningContent" type="textarea" :rows="2" /></el-form-item>''')
    io.open(P, 'w', encoding='utf-8').write(s)
    print('\n  ✓ 前端 Arrears.vue 字段改为 dunningType/dunningContent')
