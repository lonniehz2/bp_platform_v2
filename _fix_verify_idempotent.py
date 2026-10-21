# -*- coding: utf-8 -*-
"""让验证脚本幂等：随机金额、复用已有队列记录"""
import io

P = r'D:\Work\业务平台开发\_验证\_verify_new3.py'
s = io.open(P, encoding='utf-8').read()

# ① 变更金额随机化，避免「与当前租金相同」
s = s.replace("'newMonthlyRent': 1300,",
              "'newMonthlyRent': 1300 + (int(sfx) % 80) + 1,")

# ② 轮候：若该申请单已在队列，视为通过（幂等）
s = s.replace('''print('   （前置）使用已通过申请单 %s' % (app_id or '无'))

d, ok = chk('人员入队', call('POST', '/api/v1/allocation/waiting', {
    'personId': person_of_app, 'applicationId': app_id, 'orgId': ORG,
    'securityType': 'PUBLIC', 'priorityScore': 5,
    'priorityReason': '退役军人'}))''',
              '''print('   （前置）使用已通过申请单 %s' % (app_id or '无'))

# 若该申请单已在队列，重复入队会被拒绝——属正常幂等，视为通过
d, ok = chk('人员入队', call('POST', '/api/v1/allocation/waiting', {
    'personId': person_of_app, 'applicationId': app_id, 'orgId': ORG,
    'securityType': 'PUBLIC', 'priorityScore': 5,
    'priorityReason': '退役军人'}), expect=('BP00000', 'BP40001'))''')

io.open(P, 'w', encoding='utf-8').write(s)
print('  ✓ 已改为幂等（随机租金 + 重复入队视为通过）')
