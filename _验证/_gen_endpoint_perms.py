# -*- coding: utf-8 -*-
"""扫描全部 Controller，按「类级路径 + 方法语义」生成缺失的权限码。

约定：<module>:<resource>:<action>
  GET  /api/v1/fin/bills          -> fin:bill:view
  POST /api/v1/fin/bills          -> fin:bill:create
  PUT  /api/v1/fin/bills/{id}     -> fin:bill:update
  DEL  /api/v1/fin/bills/{id}     -> fin:bill:delete
  POST /api/v1/fin/bills/{id}/pay -> fin:bill:pay（子路径动词优先）

用法：python _gen_endpoint_perms.py [--apply]
"""
import io
import json
import os
import re
import sys
import urllib.request
import urllib.error

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
JAVA = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')
API = 'http://192.168.31.11:8080/api/v1'
APPLY = '--apply' in sys.argv

METHOD_ACT = {'Get': 'view', 'Post': 'create', 'Put': 'update', 'Delete': 'delete'}
VERBS = ['approve', 'audit', 'sign', 'renew', 'terminate', 'change', 'transfer', 'execute',
         'verify', 'judge', 'assign', 'grant', 'revoke', 'reset', 'issue', 'cancel',
         'pay', 'refund', 'deduct', 'calc', 'dunning', 'handle', 'close', 'read', 'done',
         'record', 'submit', 'roll', 'recalc', 'batch', 'publish', 'status', 'export',
         'import', 'scan', 'sync', 'send', 'broadcast', 'run', 'freeze', 'unfreeze',
         'query', 'detail', 'list', 'create', 'update', 'delete', 'view']

RES_ALIAS = {
    'contracts': 'contract', 'contract-changes': 'contract', 'applications': 'application',
    'terminations': 'termination', 'exchanges': 'exchange', 'allocations': 'allocation',
    'waiting': 'waitlist', 'persons': 'person', 'guarantee-profiles': 'profile',
    'verify-records': 'verify', 'houses': 'house', 'spaces': 'space', 'devices': 'device',
    'keyring': 'keyring', 'grants': 'grant', 'grant-reconcile': 'grant', 'bills': 'bill',
    'payments': 'payment', 'deposits': 'deposit', 'arrears': 'arrear', 'subsidies': 'subsidy',
    'fee-items': 'feeItem', 'dunnings': 'arrear', 'cash-flows': 'bill', 'todos': 'todo',
    'workorders': 'workorder', 'alerts': 'alert', 'complaints': 'complaint',
    'appeals': 'appeal', 'visits': 'visit', 'users': 'user', 'roles': 'role',
    'permissions': 'perm', 'dicts': 'dict', 'configs': 'config', 'audit-logs': 'audit',
    'reports': 'report', 'apps': 'app', 'open': 'app', 'gov': 'report',
    'cohabitants': 'person', 'short-rent': 'house', 'house-calendar': 'house',
}

RES_MODULE = {
    'contract': 'biz', 'application': 'biz', 'termination': 'biz', 'exchange': 'biz',
    'allocation': 'biz', 'waitlist': 'biz', 'person': 'person', 'profile': 'person',
    'verify': 'person', 'house': 'asset', 'space': 'asset', 'device': 'asset',
    'grant': 'asset', 'keyring': 'asset', 'bill': 'fin', 'payment': 'fin',
    'deposit': 'fin', 'arrear': 'fin', 'subsidy': 'fin', 'feeItem': 'fin',
    'todo': 'msg', 'workorder': 'ops', 'alert': 'ops', 'complaint': 'ops',
    'appeal': 'ops', 'visit': 'ops', 'user': 'iam', 'role': 'iam', 'perm': 'iam',
    'dict': 'sys', 'config': 'sys', 'audit': 'sys', 'report': 'rpt', 'app': 'open',
}

ACT_CN = {
    'view': '查看', 'create': '新建', 'update': '编辑', 'delete': '删除', 'export': '导出',
    'import': '导入', 'audit': '审核', 'approve': '审批', 'sign': '签约', 'renew': '续签',
    'terminate': '终止', 'change': '变更', 'transfer': '换房', 'execute': '执行',
    'status': '状态变更', 'verify': '核验', 'judge': '资格判定', 'assign': '分配',
    'grant': '授权', 'revoke': '撤销', 'reset': '重置', 'issue': '出账', 'cancel': '作废',
    'pay': '核销', 'refund': '退款', 'deduct': '抵扣', 'calc': '计算', 'dunning': '催缴',
    'handle': '处理', 'close': '结单', 'read': '标记已读', 'done': '办结', 'record': '登记',
    'submit': '报送', 'roll': '摇号', 'recalc': '重算', 'batch': '批次管理',
    'publish': '发布', 'scan': '扫描', 'sync': '同步', 'send': '发送',
    'broadcast': '广播', 'run': '执行', 'freeze': '冻结', 'unfreeze': '解冻',
    'query': '查询', 'detail': '详情', 'list': '列表',
}

RES_CN = {
    'contract': '合同', 'application': '申请', 'termination': '退租', 'exchange': '换房',
    'allocation': '配租', 'waitlist': '轮候', 'person': '人员', 'profile': '保障档案',
    'verify': '实名核验', 'house': '房源', 'space': '空间', 'device': '设备',
    'grant': '授权', 'keyring': '钥匙', 'bill': '账单', 'payment': '收款',
    'deposit': '押金', 'arrear': '催缴', 'subsidy': '补贴', 'feeItem': '计费项目',
    'todo': '待办', 'workorder': '工单', 'alert': '告警', 'complaint': '投诉',
    'appeal': '申诉', 'visit': '走访', 'user': '用户', 'role': '角色', 'perm': '权限',
    'dict': '数据字典', 'config': '系统参数', 'audit': '审计日志', 'report': '报表',
    'app': '开放应用',
}


def segments(path):
    parts = [p for p in path.split('/') if p]
    if parts and parts[0] == 'api':
        parts = parts[2:]
    return [p for p in parts if not p.startswith('{')]


def fetch(path, method='GET', body=None, token=None):
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
    token = fetch('/auth/login', 'POST',
                  {'tenantCode': '350600', 'username': 'admin', 'password': 'admin123'})['data']['token']
    have = {p['permCode'] for p in fetch('/rbac/permissions', token=token)['data']}
    print('现有权限码 %d 个' % len(have))

    found = set()
    for dirpath, _, files in os.walk(JAVA):
        for fn in files:
            if not fn.endswith('Controller.java'):
                continue
            src = io.open(os.path.join(dirpath, fn), encoding='utf-8').read()
            m = re.search(r'@RequestMapping\("([^"]+)"\)\s*public class', src)
            if not m:
                continue
            ss = segments(m.group(1))
            if not ss:
                continue
            res = RES_ALIAS.get(ss[0], ss[0])
            module = RES_MODULE.get(res, ss[0] if ss[0] in RES_MODULE.values() else '')
            if len(ss) > 1:
                res2 = RES_ALIAS.get(ss[1], ss[1])
                if res not in RES_MODULE and res2 in RES_MODULE:
                    res, module = res2, RES_MODULE[res2]
            if not module:
                module = ss[0]
            for mm in re.finditer(r'@(Get|Post|Put|Delete)Mapping(?:\("([^"]*)"\))?', src):
                kind, sub = mm.group(1), (mm.group(2) or '')
                act = METHOD_ACT.get(kind, 'view')
                low = sub.lower()
                for v in VERBS:
                    if v in low:
                        act = v
                        break
                found.add('%s:%s:%s' % (module, res, act))

    new = sorted(found - have)
    print('接口推导出权限码 %d 个，其中缺失 %d 个' % (len(found), len(new)))
    if not APPLY:
        for c in new[:15]:
            print('   [dry] ' + c)
        print('（dry-run；加 --apply 写入）')
        return 0

    ok = 0
    for code in new:
        _, res, act = code.split(':')
        name = '%s-%s' % (RES_CN.get(res, res), ACT_CN.get(act, act))
        r = fetch('/rbac/permissions', 'POST',
                  {'permCode': code, 'permName': name, 'permType': 'BUTTON', 'sortNo': 0}, token)
        if r.get('code') == 'BP00000':
            ok += 1
        else:
            print('   失败 %s -> %s' % (code, r.get('code')))
    print('已生成 %d 条权限码' % ok)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
