# -*- coding: utf-8 -*-
"""修正验证脚本：处理前置条件（已有待审批变更 / 入队需申请单）"""
import io

P = r'D:\Work\业务平台开发\_验证\_verify_new3.py'
s = io.open(P, encoding='utf-8').read()

# ① 合同变更：先清掉已有待审批的，再新建
s = s.replace('''print('=' * 70)
print(' ① 合同变更审批')
d, ok = chk('新建合同变更', call('POST', '/api/v1/contracts/%s/changes' % CONTRACT, {''',
              '''print('=' * 70)
print(' ① 合同变更审批')

# 前置：同合同只允许一条待审批变更，先把已有的处理掉
pre = call('GET', '/api/v1/contract-changes?pageNum=1&pageSize=50')
for x in ((pre[1].get('data') or {}).get('rows') or []):
    if x.get('changeStatus') in (None, 'PENDING', 'DRAFT'):
        call('POST', '/api/v1/contract-changes/%s/approve' % x['id'])
        print('   （前置）处理已有待审批变更 %s' % x.get('changeNo'))

d, ok = chk('新建合同变更', call('POST', '/api/v1/contracts/%s/changes' % CONTRACT, {''')

# ② 轮候入队：需要 applicationId
s = s.replace('''print('\\n' + '=' * 70)
print(' ② 轮候入队')
d, ok = chk('人员入队', call('POST', '/api/v1/allocation/waiting', {
    'personId': PERSON, 'orgId': ORG, 'securityType': 'PUBLIC',
    'priorityScore': 5, 'priorityReason': '退役军人'}))''',
              '''print('\\n' + '=' * 70)
print(' ② 轮候入队')

# 前置：入队必须带已通过的申请单
apps = call('GET', '/api/v1/applications?pageNum=1&pageSize=20&applicationStatus=APPROVED')
app_rows = (apps[1].get('data') or {}).get('rows') or []
app_id = app_rows[0]['id'] if app_rows else None
person_of_app = app_rows[0].get('personId') if app_rows else PERSON
print('   （前置）使用已通过申请单 %s' % (app_id or '无'))

d, ok = chk('人员入队', call('POST', '/api/v1/allocation/waiting', {
    'personId': person_of_app, 'applicationId': app_id, 'orgId': ORG,
    'securityType': 'PUBLIC', 'priorityScore': 5,
    'priorityReason': '退役军人'}))''')

io.open(P, 'w', encoding='utf-8').write(s)
print('  ✓ 已修正前置条件')
