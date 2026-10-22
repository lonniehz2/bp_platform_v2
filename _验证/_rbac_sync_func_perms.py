# -*- coding: utf-8 -*-
"""按业务补全功能权限（按钮/操作级）。

现状：只有 34 条零散功能权限，合同这类核心业务只有「签约」一条，
缺新建/编辑/删除/续签/终止等。这里按业务动作矩阵批量补齐。

权限码规则：<模块>:<资源>:<动作>，例如 biz:contract:terminate
"""
import json
import sys
import urllib.request
import urllib.error

API = 'http://192.168.31.11:8080/api/v1'
DRY = '--dry' in sys.argv

# 动作 → 中文
ACT = {
    'view': '查看', 'create': '新建', 'update': '编辑', 'delete': '删除',
    'export': '导出', 'import': '导入', 'audit': '审核', 'approve': '审批',
    'sign': '签约', 'renew': '续签', 'terminate': '终止', 'change': '变更',
    'transfer': '换房', 'execute': '执行', 'status': '状态变更',
    'verify': '核验', 'judge': '资格判定', 'assign': '分配', 'grant': '授权',
    'revoke': '撤销', 'reset': '重置密码', 'issue': '出账', 'cancel': '作废',
    'pay': '核销', 'refund': '退款', 'deduct': '抵扣', 'calc': '计算',
    'dunning': '催缴', 'handle': '处理', 'close': '结单', 'read': '标记已读',
    'done': '办结', 'record': '登记', 'submit': '报送', 'roll': '摇号',
    'recalc': '重算', 'batch': '批次管理', 'publish': '发布',
}

# 资源 → (模块, 资源名, 中文, 动作列表)
MATRIX = [
    ('biz', 'contract', '合同', ['view', 'create', 'update', 'delete', 'sign',
                                 'renew', 'terminate', 'change', 'export']),
    ('biz', 'application', '申请', ['view', 'create', 'update', 'delete',
                                    'audit', 'approve']),
    ('biz', 'termination', '退租', ['view', 'create', 'audit', 'approve', 'execute']),
    ('biz', 'exchange', '换房', ['view', 'create', 'audit', 'approve', 'execute']),
    ('biz', 'allocation', '配租', ['view', 'create', 'batch', 'roll', 'recalc']),
    ('biz', 'waitlist', '轮候', ['view', 'create', 'update', 'delete']),
    ('person', 'person', '人员', ['view', 'create', 'update', 'delete', 'status', 'export']),
    ('person', 'profile', '保障档案', ['view', 'create', 'update', 'judge', 'delete']),
    ('person', 'verify', '实名核验', ['view', 'create', 'verify']),
    ('asset', 'house', '房源', ['view', 'create', 'update', 'delete', 'status', 'import', 'export']),
    ('asset', 'space', '空间', ['view', 'create', 'update', 'delete']),
    ('asset', 'device', '设备', ['view', 'create', 'update', 'delete', 'grant']),
    ('asset', 'grant', '授权', ['view', 'grant', 'revoke']),
    ('asset', 'keyring', '钥匙', ['view', 'create', 'update', 'delete']),
    ('fin', 'bill', '账单', ['view', 'create', 'update', 'delete', 'issue', 'cancel', 'export']),
    ('fin', 'payment', '收款', ['view', 'create', 'pay', 'delete']),
    ('fin', 'deposit', '押金', ['view', 'create', 'refund', 'deduct']),
    ('fin', 'arrear', '催缴', ['view', 'create', 'dunning', 'handle']),
    ('fin', 'subsidy', '补贴', ['view', 'create', 'calc', 'pay']),
    ('fin', 'feeItem', '计费项目', ['view', 'create', 'update', 'delete']),
    ('msg', 'todo', '待办', ['view', 'create', 'read', 'done']),
    ('ops', 'workorder', '工单', ['view', 'create', 'assign', 'handle', 'close']),
    ('ops', 'alert', '告警', ['view', 'create', 'handle']),
    ('ops', 'complaint', '投诉', ['view', 'create', 'handle']),
    ('ops', 'appeal', '申诉', ['view', 'create', 'handle']),
    ('ops', 'visit', '走访', ['view', 'create', 'record']),
    ('iam', 'user', '用户', ['view', 'create', 'update', 'delete', 'assign', 'reset']),
    ('iam', 'role', '角色', ['view', 'create', 'update', 'delete', 'assign']),
    ('iam', 'perm', '权限', ['view', 'create', 'update', 'delete']),
    ('sys', 'dict', '数据字典', ['view', 'create', 'update', 'delete']),
    ('sys', 'config', '系统参数', ['view', 'update']),
    ('sys', 'audit', '审计日志', ['view', 'export']),
    ('rpt', 'report', '报表', ['view', 'export']),
    ('open', 'app', '开放应用', ['view', 'create', 'update', 'status']),
    ('gov', 'report', '监管报送', ['view', 'submit']),
]


def call(path, method='GET', body=None, token=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=data, method=method)
    r.add_header('Content-Type', 'application/json')
    r.add_header('X-Tenant-Id', '350600')
    if token:
        r.add_header('Authorization', 'Bearer ' + token)
    try:
        with urllib.request.urlopen(r, timeout=60) as x:
            return json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {'code': 'HTTP%d' % e.code}


def main():
    token = call('/auth/login', 'POST',
                 {'tenantCode': '350600', 'username': 'admin', 'password': 'admin123'})['data']['token']
    perms = call('/rbac/permissions', token=token)['data']
    have = {p['permCode'] for p in perms}
    print('现有权限 %d 条' % len(perms))

    created = skipped = 0
    for module, resource, res_name, actions in MATRIX:
        for act in actions:
            code = '%s:%s:%s' % (module, resource, act)
            if code in have:
                skipped += 1
                continue
            name = '%s-%s' % (res_name, ACT.get(act, act))
            if DRY:
                print('   [dry] %s（%s）' % (code, name))
                created += 1
                continue
            r = call('/rbac/permissions', 'POST',
                     {'permCode': code, 'permName': name, 'permType': 'BUTTON', 'sortNo': 0},
                     token)
            if r.get('code') == 'BP00000':
                created += 1
            else:
                print('   失败 %s -> %s %s' % (code, r.get('code'), r.get('message')))
    print('新增功能权限 %d 条，已存在跳过 %d 条' % (created, skipped))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
