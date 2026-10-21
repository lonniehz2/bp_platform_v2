# -*- coding: utf-8 -*-
"""给扩展操作台的各「新增」按钮接上真实表单弹窗"""
import io
import re

P = r'D:\Work\业务平台开发\frontend\src\views\OpsExtras.vue'
s = io.open(P, encoding='utf-8').read()

# 用通用 JSON 弹窗实现所有「新增」，避免字段猜测风险：
# 通过替换按钮点击逻辑，改为调用 openJson(...)
REPLACE = [
    ('@click="msgSendVisible = true"',
     '''@click="openJson('发送消息', '按模板发送站内信/短信/微信；接收人类型 PERSON/USER/ORG',
       '/messages/send', { templateCode: 'CONTRACT_EFFECTIVE', bizType: 'CONTRACT',
       bizId: 1, channel: 'INNER', receiverType: 'PERSON', receiverId: '1',
       title: '标题', content: '内容' })"'''),
    ('@click="todoCreateVisible = true"',
     '''@click="openJson('新增待办', '给指定用户生成一条待办', '/messages/todos',
       { userId: 1, todoType: 'APPROVAL', title: '待办标题', content: '内容',
       bizType: 'APPLICATION', bizId: 1, dueTime: '2026-12-31 18:00:00' })"'''),
    ('@click="rulesetVisible = true"',
     '''@click="openJson('新增规则集', '规则集是一组阈值规则的容器，发布后才参与评估',
       '/rules/rulesets', { code: 'RS_FIN_2', name: '欠费规则集', domain: 'FINANCE',
       scenario: 'ARREAR', securityType: 'PUBLIC', version: 'v1',
       description: '说明' })"'''),
    ('@click="ruleVisible = true"',
     '''@click="openJson('新增规则', '需先选中规则集（点行内「加规则」）', 
       '/rules/rulesets/' + (currentRuleset.value?.id || 0) + '/rules',
       { code: 'R_ARREAR_1', name: '欠费比例告警', conditionExpr: 'arrearRate > 15',
       thresholdJson: '{"threshold":15}', severity: 'WARNING',
       eventType: 'ARREAR_RATE' })"'''),
    ('@click="hookVisible = true"',
     '''@click="openJson('新增 Webhook', '事件类型用英文逗号分隔，如 contract.effective,payment.paid',
       '/open/webhooks', { hookName: '测试回调', callbackUrl: 'https://example.com/cb',
       eventTypes: 'contract.effective', retryTimes: 3, hookStatus: 'ENABLED' })"'''),
    ('@click="userVisible = true"',
     '''@click="openJson('新增用户', '密码会走 PBKDF2 加密存储',
       '/rbac/users', { username: 'newuser', password: 'Passw0rd!', realName: '新用户',
       orgId: 1, userType: 'STAFF' })"'''),
    ('@click="roleVisible = true"',
     '''@click="openJson('新增角色', 'dataScope：ALL/DEPT/SELF',
       '/rbac/roles', { roleCode: 'AUDITOR', roleName: '稽核员', dataScope: 'ALL' })"'''),
    ('@click="permVisible = true"',
     '''@click="openJson('新增权限', 'permType：API/MENU/BUTTON/DATA',
       '/rbac/permissions', { parentId: null, permCode: 'fin:audit:view',
       permName: '稽核查账', permType: 'API', routePath: '', sortNo: 99 })"'''),
]

n = 0
for old, new in REPLACE:
    if old in s:
        s = s.replace(old, new, 1)
        n += 1
print('  ✓ 替换 %d 个按钮为真实提交弹窗' % n)

# 房态 4 个按钮接上
CAL = [
    ('@click="calPriceVisible = true"',
     '''@click="openJson('修改日房价', '指定日期改价', 
       '/house-calendar/' + cal.houseId + '/price',
       { calendarDate: '2026-11-01', price: 220.00 })"'''),
    ('@click="calStatusVisible = true"',
     '''@click="openJson('修改日房态', 'dayStatus：FREE/FULL/LOCKED/CLOSED',
       '/house-calendar/' + cal.houseId + '/status',
       { calendarDate: '2026-11-01', dayStatus: 'LOCKED' })"'''),
    ('@click="calBookVisible = true"',
     '''@click="openJson('预订房态', '短租预订占用某天', '/house-calendar/book',
       { houseId: 1, startDate: '2026-11-01', endDate: '2026-11-03',
       orderId: 1, guestName: '客人' })"'''),
    ('@click="calReleaseVisible = true"',
     '''@click="openJson('释放房态', '取消预订/占用', '/house-calendar/release',
       { houseId: 1, startDate: '2026-11-01', endDate: '2026-11-03' })"'''),
]
for old, new in CAL:
    if old in s:
        s = s.replace(old, new, 1)
        n += 1

# 规则弹窗需要 currentRuleset，点击「加规则」已设置；避免未选中时报错
s = s.replace("""function execRuleset(row) {""",
              """function execRuleset(row) {
  currentRuleset.value = row""", 1)

io.open(P, 'w', encoding='utf-8').write(s)
print('  ✓ 共 %d 个操作已接真实提交' % n)

# 语法自检：单引号嵌套在模板属性里会破坏模板
bad = len(re.findall(r'@click="openJson\(\'', s))
print('  模板内 openJson 调用：%d 处' % bad)
