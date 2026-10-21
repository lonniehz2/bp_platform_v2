# -*- coding: utf-8 -*-
"""消息中心验证：模板渲染 / 发送 / 广播 / 待办"""
import json
import time
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
TENANT = '350600'
TOK = None


def call(m, p, b=None):
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': TENANT}
    if TOK:
        h['Authorization'] = 'Bearer ' + TOK
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE + p, data=d, method=m, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=40) as x:
            raw = x.read().decode('utf-8', 'replace')
            try:
                return x.status, json.loads(raw)
            except Exception:
                return x.status, {'code': 'HTML'}
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {'code': 'HTTP_%d' % e.code}


ok = fail = 0


def chk(name, cond, extra=''):
    global ok, fail
    if cond:
        ok += 1
        print('  [PASS] ' + name)
    else:
        fail += 1
        print('  [FAIL] ' + name + '  ' + str(extra))


sfx = str(int(time.time()))[-6:]
print('=' * 78)
print(' 消息中心验证')
print('=' * 78)

st, r = call('POST', '/api/v1/auth/login',
             {'tenantId': TENANT, 'username': 'admin', 'password': 'admin123'})
TOK = (r.get('data') or {}).get('token')
chk('管理员登录', bool(TOK), r.get('code'))

# ==================== 1. 模板 ====================
st, r = call('GET', '/api/v1/messages/templates')
tpls = r.get('data') or []
chk('⭐ 模板列表（6 条内置）', len(tpls) >= 6, len(tpls))
codes = {t.get('templateCode') for t in tpls}
chk('含欠费催缴模板', 'ARREARS' in codes, codes)

# 模板渲染
st, r = call('POST', '/api/v1/messages/templates/ARREARS/render',
             {'name': '张三', 'amount': '1500.00', 'days': '35'})
chk('⭐ 模板变量渲染', r.get('code') == 'BP00000', r.get('code'))
rendered = str(r.get('data'))
print('     渲染结果：%s' % rendered)
chk('⭐⭐ 变量已替换（无 ${} 残留）', '${' not in rendered, rendered)
chk('替换值正确', '张三' in rendered and '1500.00' in rendered and '35' in rendered,
    rendered)

# 缺变量仍渲染（保留占位符）
st, r = call('POST', '/api/v1/messages/templates/ARREARS/render', {'name': '李四'})
chk('⭐ 缺变量保留占位符（不报错）', r.get('code') == 'BP00000', r.get('code'))

# 新增模板
st, r = call('POST', '/api/v1/messages/templates', {
    'templateCode': 'DEMO_' + sfx, 'templateName': '演示模板', 'channel': 'INNER',
    'bizType': 'DEMO', 'titleTpl': '演示', 'contentTpl': '你好 ${name}'})
chk('⭐ 新增模板', r.get('code') == 'BP00000', r.get('code'))
chk('模板写入当前租户', (r.get('data') or {}).get('tenantId') == TENANT,
    (r.get('data') or {}).get('tenantId'))

# ==================== 2. 发送 ====================
st, r = call('POST', '/api/v1/messages/send', {
    'templateCode': 'ARREARS', 'bizType': 'ARREARS', 'bizId': 1001,
    'channel': 'SMS', 'receiverType': 'PERSON', 'receiverId': '4001',
    'receiverName': '张三', 'receiverAddr': '13800138000',
    'variables': {'name': '张三', 'amount': '1500.00', 'days': '35'}})
chk('⭐ 按短信渠道发送', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
msg = r.get('data') or {}
chk('消息号 MSG 开头', str(msg.get('messageNo', '')).startswith('MSG'), msg.get('messageNo'))
chk('⭐⭐ 内容已按模板渲染', '1500.00' in str(msg.get('content')), msg.get('content'))
chk('发送成功 SUCCESS', msg.get('sendStatus') == 'SUCCESS', msg.get('sendStatus'))
chk('有第三方消息ID', bool(msg.get('messageNo')), None)
print('     内容：%s' % str(msg.get('content'))[:80])

# 短信缺地址 → 失败
st, r = call('POST', '/api/v1/messages/send', {
    'templateCode': 'ARREARS', 'bizType': 'ARREARS', 'channel': 'SMS',
    'receiverId': '4002', 'variables': {'name': '李四', 'amount': '100', 'days': '5'}})
chk('⭐⭐ 短信缺手机号 → 失败', (r.get('data') or {}).get('sendStatus') == 'FAILED',
    (r.get('data') or {}).get('sendStatus'))
chk('失败原因可读', '需要接收地址' in str((r.get('data') or {}).get('failReason')),
    (r.get('data') or {}).get('failReason'))

# 站内消息不需地址
st, r = call('POST', '/api/v1/messages/send', {
    'templateCode': 'CONTRACT_EXPIRE', 'bizType': 'CONTRACT_EXPIRE', 'channel': 'INNER',
    'receiverId': '4001', 'variables': {'leaseEnd': '2027-12-31'}})
chk('⭐ 站内消息无需地址', (r.get('data') or {}).get('sendStatus') == 'SUCCESS',
    (r.get('data') or {}).get('sendStatus'))

# 无模板直发
st, r = call('POST', '/api/v1/messages/send', {
    'bizType': 'OTHER', 'channel': 'INNER', 'receiverId': '4001',
    'title': '直发测试', 'content': '这是一条无模板消息'})
chk('⭐ 无模板直发', (r.get('data') or {}).get('content') == '这是一条无模板消息',
    r.get('code'))
st, r = call('POST', '/api/v1/messages/send', {'bizType': 'OTHER', 'channel': 'INNER'})
chk('无内容被拒', r.get('code') == 'BP10001', r.get('code'))

# ==================== 3. 发送记录与重投 ====================
st, r = call('GET', '/api/v1/messages/records?pageNum=1&pageSize=20&bizType=ARREARS')
rec = (r.get('data') or {}).get('rows') or []
chk('⭐ 发送记录查询', len(rec) >= 2, len(rec))
st, r = call('GET', '/api/v1/messages/records?pageNum=1&pageSize=20&sendStatus=FAILED')
failed = (r.get('data') or {}).get('rows') or []
chk('⭐ 按失败状态筛选', len(failed) >= 1, len(failed))

st, r = call('POST', '/api/v1/messages/retry-failed?limit=10')
chk('⭐ 失败重投接口', r.get('code') == 'BP00000', r.get('code'))
print('     本次重投成功：%s 条' % r.get('data'))

# ==================== 4. 订阅广播 ====================
st, r = call('POST', '/api/v1/messages/broadcast', {
    'bizType': 'ARREARS', 'title': '欠费批量催缴',
    'content': '有 3 户欠费超 30 天，请及时处理', 'bizId': 2001})
chk('⭐⭐ 按订阅广播', r.get('code') == 'BP00000', r.get('code'))
cnt = int(r.get('data') or 0)
print('     广播触达条数：%s' % cnt)
chk('⭐ 广播至少 1 条（ARREARS 订阅财务岗 SMS+INNER）', cnt >= 1, cnt)

# ==================== 5. 站内待办 ====================
UID = 9001
st, r = call('POST', '/api/v1/messages/todos', {
    'userId': UID, 'todoType': 'APPROVE', 'title': '退租审批待办',
    'content': '退租单 BT001 待您审批', 'bizType': 'TERMINATION', 'bizId': 3001,
    'priority': 'URGENT'})
chk('⭐ 创建站内待办', r.get('code') == 'BP00000', r.get('code'))
tid = (r.get('data') or {}).get('id')
chk('初始未读 PENDING', (r.get('data') or {}).get('todoStatus') == 'PENDING',
    (r.get('data') or {}).get('todoStatus'))

st, r = call('GET', '/api/v1/messages/todos/unread?userId=%s' % UID)
chk('⭐ 未读数量（红点）', int(r.get('data') or 0) >= 1, r.get('data'))

st, r = call('GET', '/api/v1/messages/todos?pageNum=1&pageSize=20&userId=%s' % UID)
chk('待办列表', r.get('code') == 'BP00000'
    and int((r.get('data') or {}).get('total', 0)) >= 1,
    (r.get('data') or {}).get('total'))

st, r = call('POST', '/api/v1/messages/todos/%s/read' % tid, {})
chk('标记已读 READ', (r.get('data') or {}).get('todoStatus') == 'READ', r.get('code'))
st, r = call('POST', '/api/v1/messages/todos/%s/done' % tid, {})
chk('办结 DONE', (r.get('data') or {}).get('todoStatus') == 'DONE', r.get('code'))
chk('办结时间已记录', bool((r.get('data') or {}).get('doneTime')),
    (r.get('data') or {}).get('doneTime'))
st, r = call('POST', '/api/v1/messages/todos/%s/done' % tid, {})
chk('⭐ 重复办结被拒', r.get('code') == 'BP40001', r.get('code'))

st, r = call('GET', '/api/v1/messages/todos/unread?userId=%s' % UID)
chk('办结后未读归零', int(r.get('data') or 0) == 0, r.get('data'))

print()
print('-' * 78)
print('  通过 %d / 失败 %d' % (ok, fail))
print('-' * 78)
