# -*- coding: utf-8 -*-
"""重新生成 OpsExtras.vue 并用「函数式」接上所有新增入口"""
import io
import re
import subprocess
import sys

GEN = r'D:\Work\业务平台开发\_gen_ops_extras.py'
subprocess.run([sys.executable, GEN], cwd=r'D:\Work\业务平台开发')

P = r'D:\Work\业务平台开发\frontend\src\views\OpsExtras.vue'
s = io.open(P, encoding='utf-8').read()

# 1) 模板：按钮改为调用函数
BTN = {
    'msgSendVisible = true': 'openMsgSend()',
    'todoCreateVisible = true': 'openTodoCreate()',
    'rulesetVisible = true': 'openRulesetCreate()',
    'ruleVisible = true': 'openRuleCreate()',
    'hookVisible = true': 'openHookCreate()',
    'userVisible = true': 'openUserCreate()',
    'roleVisible = true': 'openRoleCreate()',
    'permVisible = true': 'openPermCreate()',
    'calPriceVisible = true': 'openCalPrice()',
    'calStatusVisible = true': 'openCalStatus()',
    'calBookVisible = true': 'openCalBook()',
    'calReleaseVisible = true': 'openCalRelease()',
}
for old, new in BTN.items():
    s = s.replace('@click="%s"' % old, '@click="%s"' % new)

# 2) 脚本：注入函数定义
FUNCS = '''
// ---------- 各模块「新增」入口（统一走 JSON 弹窗，字段取自后端 DTO） ----------
function openMsgSend() {
  openJson('发送消息', '按模板发送；接收人类型 PERSON/USER/ORG',
    '/messages/send',
    { templateCode: 'CONTRACT_EFFECTIVE', bizType: 'CONTRACT', bizId: 1,
      channel: 'INNER', receiverType: 'PERSON', receiverId: '1',
      title: '标题', content: '内容' })
}
function openTodoCreate() {
  openJson('新增待办', '给指定用户生成一条待办',
    '/messages/todos',
    { userId: 1, todoType: 'APPROVAL', title: '待办标题', content: '内容',
      bizType: 'APPLICATION', bizId: 1, dueTime: '2026-12-31 18:00:00' })
}
function openRulesetCreate() {
  openJson('新增规则集', '规则集是阈值规则的容器，发布后才参与评估',
    '/rules/rulesets',
    { code: 'RS_FIN_2', name: '欠费规则集', domain: 'FINANCE',
      scenario: 'ARREAR', securityType: 'PUBLIC', version: 'v1',
      description: '说明' })
}
function openRuleCreate() {
  if (!currentRuleset.value) {
    ElMessage.warning('请先在规则集行内点「加规则」')
    return
  }
  openJson('新增规则', '条件表达式 + 阈值 JSON',
    `/rules/rulesets/${currentRuleset.value.id}/rules`,
    { code: 'R_ARREAR_1', name: '欠费比例告警', conditionExpr: 'arrearRate > 15',
      thresholdJson: '{"threshold":15}', severity: 'WARNING',
      eventType: 'ARREAR_RATE' })
}
function openHookCreate() {
  openJson('新增 Webhook', '事件类型用英文逗号分隔',
    '/open/webhooks',
    { hookName: '测试回调', callbackUrl: 'https://example.com/cb',
      eventTypes: 'contract.effective', retryTimes: 3, hookStatus: 'ENABLED' })
}
function openUserCreate() {
  openJson('新增用户', '密码走 PBKDF2 加密存储',
    '/rbac/users',
    { username: 'newuser', password: 'Passw0rd!', realName: '新用户',
      orgId: 1, userType: 'STAFF' })
}
function openRoleCreate() {
  openJson('新增角色', 'dataScope：ALL / DEPT / SELF',
    '/rbac/roles',
    { roleCode: 'AUDITOR', roleName: '稽核员', dataScope: 'ALL' })
}
function openPermCreate() {
  openJson('新增权限', 'permType：API / MENU / BUTTON / DATA',
    '/rbac/permissions',
    { parentId: null, permCode: 'fin:audit:view', permName: '稽核查账',
      permType: 'API', routePath: '', sortNo: 99 })
}
function openCalPrice() {
  if (!cal.houseId) { ElMessage.warning('请先填房源ID'); return }
  openJson('修改日房价', '指定日期改价',
    `/house-calendar/${cal.houseId}/price`,
    { calendarDate: '2026-11-01', price: 220.00 })
}
function openCalStatus() {
  if (!cal.houseId) { ElMessage.warning('请先填房源ID'); return }
  openJson('修改日房态', 'dayStatus：FREE / FULL / LOCKED / CLOSED',
    `/house-calendar/${cal.houseId}/status`,
    { calendarDate: '2026-11-01', dayStatus: 'LOCKED' })
}
function openCalBook() {
  openJson('预订房态', '短租预订占用某段日期',
    '/house-calendar/book',
    { houseId: 1, startDate: '2026-11-01', endDate: '2026-11-03',
      orderId: 1, guestName: '客人' })
}
function openCalRelease() {
  openJson('释放房态', '取消预订/占用',
    '/house-calendar/release',
    { houseId: 1, startDate: '2026-11-01', endDate: '2026-11-03' })
}

'''

s = s.replace('function openJson(', FUNCS + 'function openJson(', 1)

# 3) 移除不再使用的 ref（避免告警）
for dead in ('msgSendVisible', 'todoCreateVisible', 'rulesetVisible', 'ruleVisible',
             'hookVisible', 'userVisible', 'roleVisible', 'permVisible',
             'calPriceVisible', 'calStatusVisible', 'calBookVisible',
             'calReleaseVisible'):
    s = re.sub(r'const %s = ref\(false\)\n' % dead, '', s)

io.open(P, 'w', encoding='utf-8').write(s)
print('  ✓ OpsExtras.vue 12 个入口改为函数式调用')

left = re.findall(r'@click="(\w+Visible = true)"', s)
print('  仍为直接置位的按钮：%s' % (left or '无'))
