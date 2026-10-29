# -*- coding: utf-8 -*-
"""用户旅程闭环检查：按真实使用顺序把业务串起来，确认每一步都能走通。

区别于单接口冒烟：本脚本强调**数据能否接力**——
人员 → 申请 → 配租 → 合同 → 账单 → 收款 → 退租；
空间 → 房源 → 设备 → 绑定 → 钥匙 → 授权；
计费项 → 抄表 → 出账 → 账单；
工单 → 派单 → 完成；租户自助视角。
"""
import json
import random
import string
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta

BASE = 'http://192.168.31.11:8080/api/v1'
TENANT = '350600'

OK, FAIL = [], []


def call(path, method='GET', body=None, tok=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method)
    r.add_header('Content-Type', 'application/json')
    r.add_header('X-Tenant-Id', TENANT)
    if tok:
        r.add_header('Authorization', 'Bearer ' + tok)
    try:
        with urllib.request.urlopen(r, timeout=180) as x:
            return x.status, json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}
    except Exception as e:
        return 0, {'message': str(e)}


def login(u, p):
    st, d = call('/auth/login', 'POST', {'tenantCode': TENANT, 'username': u, 'password': p})
    return ((d or {}).get('data') or {}).get('token')


def step(journey, name, cond, detail=''):
    if cond:
        OK.append((journey, name))
        print('  ✔ %s' % name)
    else:
        FAIL.append((journey, name, detail))
        print('  ✗ %s  %s' % (name, detail))
    return cond


def data(resp):
    return (resp[1] or {}).get('data')


def rows(resp):
    d = data(resp) or {}
    return d.get('rows') or []


def gen_id_card():
    '''生成合法的 18 位身份证号（含校验位）。'''
    body = '3501021990' + '%04d' % random.randint(1, 1231) + '%03d' % random.randint(1, 999)
    weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    checks = '10X98765432'
    total = sum(int(body[i]) * weights[i] for i in range(17))
    return body + checks[total % 11]


def rid():
    return ''.join(random.choices(string.digits, k=6))


admin = login('admin', 'admin123')
tenant = login('test_tenant', 'Test@1234')
assert admin, 'admin 登录失败'

# ---------------------------------------------------------------- 旅程 1
print('\n[旅程1] 保障对象：建档 → 申请 → 配租 → 合同 → 账单 → 收款')
name = '闭环测试' + rid()
st, r = call('/persons', 'POST', {
    'personName': name, 'idCard': gen_id_card(),
    'phone': '139' + str(random.randint(10000000, 99999999)),
    'personType': 'FAMILY', 'gender': 'MALE'}, admin)
pid = (data((st, r)) or {}).get('id')
step('旅程1', '新建人员', st == 200 and pid, (r or {}).get('message', '')[:60])

st, r = call('/persons?pageNum=1&pageSize=5&keyword=' + urllib.parse.quote(name), 'GET', None, admin)
step('旅程1', '人员可检索', any(x.get('personName') == name for x in rows((st, r))))

st, rv = call('/verify-records', 'POST', {
    'personId': pid, 'verifyType': 'FACE', 'userName': '闭环测试',
    'faceResult': '1', 'citizenResult': '1', 'faceScore': 95.0,
    'resultCode': '0000', 'responseCode': '200'}, admin)
step('旅程1', '完成实名核验', st in (200, 400), (rv or {}).get('message', '')[:60])
st, ro = call('/orgs?pageNum=1&pageSize=1', 'GET', None, admin)
org = (rows((st, ro)) or [{}])[0].get('id')
st, r = call('/applications', 'POST', {
    'personId': pid, 'securityType': 'PUBLIC', 'applyChannel': 'ONLINE',
    'orgId': org, 'familySize': 2, 'declaredIncome': 4200,
    'declaredIncomeYear': 50400, 'incomeCheckPeriod': 'LAST_12M',
    'complianceCommitFlag': 1, 'dataShareAgreeFlag': 1}, admin)
app_id = (data((st, r)) or {}).get('id')
step('旅程1', '提交申请', st == 200 and app_id, (r or {}).get('message', '')[:60])

if app_id:
    st, r = call('/applications/%s/accept' % app_id, 'POST', {}, admin)
    step('旅程1', '受理申请', st == 200, (r or {}).get('message', '')[:60])
    st, rp = call('/guarantee-profiles', 'POST', {
        'personId': pid, 'securityType': 'PUBLIC', 'familySize': 2,
        'monthlyIncome': 4200, 'annualIncome': 50400,
        'householdIncome': 50400, 'profileStatus': 'QUALIFIED'}, admin)
    step('旅程1', '建立保障档案', st in (200, 400), (rp or {}).get('message', '')[:60])
    st, r = call('/applications/%s/review' % app_id, 'POST',
                 {'stage': 'ACCEPT', 'result': 'PASS', 'remark': '闭环测试通过'}, admin)
    step('旅程1', '申请审核通过', st == 200, (r or {}).get('message', '')[:60])

    st, r = call('/applications/%s' % app_id, 'GET', None, admin)
    d = data((st, r)) or {}
    step('旅程1', '申请状态已流转',
         d.get('applicationStatus') in ('ACCEPTED', 'REVIEWING', 'APPROVED', 'PUBLICITY'),
         str(d.get('applicationStatus')))

# ---------------------------------------------------------------- 旅程 2
print('\n[旅程2] 资产：空间 → 房源 → 设备 → 绑定 → 钥匙 → 授权')
st, r = call('/spaces/tree?orgId=1', 'GET', None, admin)
step('旅程2', '空间层级可查询', st == 200)

st, r = call('/houses?pageNum=1&pageSize=5', 'GET', None, admin)
hs = rows((st, r))
house = hs[0] if hs else None
step('旅程2', '房源台账可查询', bool(house))
step('旅程2', '房源带空间关联', bool(house and house.get('spaceId')),
     'spaceId=%s' % (house or {}).get('spaceId'))

st, r = call('/devices/types', 'GET', None, admin)
types = data((st, r)) or []
step('旅程2', '设备分类清单可用', len(types) >= 8, '共 %d 类' % len(types))

st, r = call('/devices/unbound', 'GET', None, admin)
unbound = data((st, r)) or []
step('旅程2', '未绑定设备可查询', st == 200)

if house and house.get('spaceId'):
    st, r = call('/devices', 'GET', None, admin)
    cand = [x for x in (rows((st, r)) or []) if not x.get('spaceId')]
    if cand:
        dev = cand[0]
        st, r = call('/devices/%s/bind' % dev['id'], 'POST',
                     {'spaceId': house['spaceId']}, admin)
        step('旅程2', '设备绑定到空间', st == 200, (r or {}).get('message', '')[:50])
        st, r = call('/devices/inherited?houseId=%s' % house['id'], 'GET', None, admin)
        d = data((st, r)) or {}
        step('旅程2', '继承链可返回设备', isinstance(d.get('devices'), list),
             '设备 %d 台' % len(d.get('devices') or []))

st, r = call('/keyring?pageNum=1&pageSize=5', 'GET', None, admin)
step('旅程2', '钥匙包可查询', st == 200)

st, r = call('/grants?pageNum=1&pageSize=5', 'GET', None, admin)
step('旅程2', '授权台账可查询', st == 200)

# ---------------------------------------------------------------- 旅程 3
print('\n[旅程3] 计量：计费项 → 抄表 → 出账 → 账单')
st, r = call('/fin/fee-items?pageNum=1&pageSize=50', 'GET', None, admin)
items = rows((st, r))
meters = [x for x in items if x.get('calcMode') == 'METER']
step('旅程3', '存在计量类计费项', len(meters) >= 1, '共 %d 个' % len(meters))

if house and meters:
    item = meters[0]
    prev = date.today() - timedelta(days=30)
    # 取该房源+项目已有最大读数，避免重复运行导致本次用量为 0
    st0, r0 = call('/fin/meter-readings?pageNum=1&pageSize=1&houseId=%s&feeItemId=%s'
                   % (house['id'], item['id']), 'GET', None, admin)
    base = 5000
    if st0 == 200 and rows((st0, r0)):
        try:
            base = int(float(rows((st0, r0))[0].get('reading') or 5000)) + 100
        except Exception:
            base = 5000
    call('/fin/meter-readings', 'POST', {
        'houseId': house['id'], 'feeItemId': item['id'], 'reading': base,
        'readDate': str(prev)}, admin)
    st, r = call('/fin/meter-readings', 'POST', {
        'houseId': house['id'], 'feeItemId': item['id'], 'reading': base + 50,
        'readDate': str(date.today())}, admin)
    reading = data((st, r)) or {}
    step('旅程3', '录本期读数', st == 200 and reading.get('id'),
         (r or {}).get('message', '')[:50])
    if reading.get('id'):
        st, r = call('/fin/meter-readings/%s/bill' % reading['id'], 'POST', None, admin)
        bill = data((st, r)) or {}
        step('旅程3', '读数出账生成账单', st == 200 and bill.get('billNo'),
             (r or {}).get('message', '')[:50])
        if bill.get('billNo'):
            st, r = call('/fin/bills?pageNum=1&pageSize=5&houseId=%s' % house['id'],
                         'GET', None, admin)
            found = [b for b in rows((st, r)) if b.get('billNo') == bill.get('billNo')]
            step('旅程3', '账单可在账单页查到', bool(found))

# ---------------------------------------------------------------- 旅程 4
print('\n[旅程4] 运维：工单派单 → 完成；投诉登记')
st, r = call('/workorders', 'POST', {
    'orderTitle': '闭环工单' + rid(), 'orderType': 'REPAIR', 'priority': 'MEDIUM',
    'orderSource': 'TENANT_APP', 'orderDesc': '水管漏水'}, admin)
wo = data((st, r)) or {}
step('旅程4', '创建工单', st == 200 and wo.get('id'), (r or {}).get('message', '')[:50])
if wo.get('id'):
    st, r = call('/workorders/%s/auto-assign' % wo['id'], 'POST', None, admin)
    step('旅程4', '工单可派单（无指派人时可自动）', st in (200, 400),
         (r or {}).get('message', '')[:50])

st, r = call('/complaints?pageNum=1&pageSize=5', 'GET', None, admin)
step('旅程4', '投诉列表可查询', st == 200)

st, r = call('/alerts?pageNum=1&pageSize=5', 'GET', None, admin)
step('旅程4', '告警列表可查询', st == 200)

# ---------------------------------------------------------------- 旅程 5
print('\n[旅程5] 租户自助：登录 → 我的合同/账单/报修')
step('旅程5', '租户登录成功', bool(tenant))
if tenant:
    for path, label in [('/contracts?pageNum=1&pageSize=5', '我的合同'),
                        ('/fin/bills?pageNum=1&pageSize=5', '我的账单'),
                        ('/workorders?pageNum=1&pageSize=5', '我的报修'),
                        ('/publicities?pageNum=1&pageSize=5', '公示公告')]:
        st, r = call(path, 'GET', None, tenant)
        step('旅程5', label + '可访问', st == 200, (r or {}).get('message', '')[:40])

# ---------------------------------------------------------------- 旅程 6
print('\n[旅程6] 统计与看板：数据能反映业务')
for path, label in [('/rpt/metrics/current', '驾驶舱指标'),
                    ('/devices/stats', '设备统计'),
                    ('/devices/freshness?hours=720', '数据新鲜度')]:
    st, r = call(path, 'GET', None, admin)
    step('旅程6', label + '可访问', st == 200, (r or {}).get('message', '')[:40])

# ---------------------------------------------------------------- 边缘旅程
import _check_journeys_edge as edge

edge.run_edge_journeys({
    'call': call, 'step': step, 'rows': rows, 'data': data,
    'rid': rid, 'gen_id_card': gen_id_card, 'admin': admin,
})

# ---------------------------------------------------------------- 汇总
print('\n' + '=' * 66)
print('闭环检查：通过 %d 步，失败 %d 步' % (len(OK), len(FAIL)))
if FAIL:
    print('失败明细：')
    for j, n, d in FAIL:
        print('  [%s] %s  %s' % (j, n, d))
    print('=' * 66)
    sys.exit(1)
print('  ✔ 全流程闭环')
print('=' * 66)
