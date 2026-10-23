# -*- coding: utf-8 -*-
"""权限推导唯一规则源 + 公开接口白名单 + 一键同步。

被 _perm_sync.py 使用；规则集中在此，避免「生成端」与「注解端」推导不一致。

推导规则：<module>:<resource>:<action>
  module   = 类级路径第一段；若该段不是已知模块，则按 resource 反查
  resource = 类级路径第二段（别名归一）；类级路径只有模块时取方法子路径首段
  action   = GET=view / POST=create / PUT=update / DELETE=delete；
             子路径出现 approve/audit/sign/... 等动词时优先用动词
"""

import re

MODULES = {'biz', 'fin', 'asset', 'person', 'iam', 'sys', 'msg', 'ops', 'rpt', 'open', 'gov'}

RES_ALIAS = {
    # 复数 → 单数
    'contracts': 'contract', 'applications': 'application', 'terminations': 'termination',
    'exchanges': 'exchange', 'allocations': 'allocation', 'waitlists': 'waitlist',
    'houses': 'house', 'spaces': 'space', 'devices': 'device', 'persons': 'person',
    'bills': 'bill', 'payments': 'payment', 'deposits': 'deposit', 'arrears': 'arrear',
    'subsidies': 'subsidy', 'workorders': 'workorder', 'complaints': 'complaint',
    'appeals': 'appeal', 'visits': 'visit', 'users': 'user', 'roles': 'role',
    'permissions': 'perm', 'orgs': 'org', 'alerts': 'alert', 'todos': 'todo',
    'files': 'file', 'rules': 'rule', 'grants': 'grant',
    # 复合 → 规范资源
    'contract-changes': 'contract', 'guarantee-profiles': 'profile',
    'access-records': 'access', 'house-calendar': 'house',
    'grant-reconcile': 'grant', 'verify-records': 'verify',
    'publicities': 'publicity', 'short-rent-orders': 'shortRent',
    'meter-readings': 'meterReading', 'inspection-plans': 'inspectionPlan',
    'cohabitants': 'cohabitant', 'fee-items': 'feeItem', 'cash-flows': 'cashFlow',
    'audit-logs': 'audit', 'rule-engine': 'rule', 'annual-reviews': 'annualReview',
}

RES_MODULE = {
    'contract': 'biz', 'application': 'biz', 'termination': 'biz', 'exchange': 'biz',
    'allocation': 'biz', 'waitlist': 'biz', 'contractChange': 'biz', 'cohabitant': 'biz',
    'publicity': 'biz', 'shortRent': 'biz',
    'person': 'person', 'profile': 'person', 'verify': 'person',
    'house': 'asset', 'space': 'asset', 'device': 'asset', 'grant': 'asset',
    'keyring': 'asset', 'access': 'asset',
    'bill': 'fin', 'payment': 'fin', 'deposit': 'fin', 'arrear': 'fin',
    'subsidy': 'fin', 'feeItem': 'fin', 'cashFlow': 'fin', 'meterReading': 'fin',
    'todo': 'msg', 'workorder': 'ops', 'alert': 'ops', 'complaint': 'ops',
    'appeal': 'ops', 'visit': 'ops', 'rule': 'ops', 'inspectionPlan': 'ops',
    'user': 'iam', 'role': 'iam', 'perm': 'iam', 'org': 'iam',
    'dict': 'sys', 'config': 'sys', 'audit': 'sys', 'file': 'sys',
    'report': 'rpt', 'app': 'open', 'annualReview': 'biz',
}

METHOD_ACTION = {'Get': 'view', 'Post': 'create', 'Put': 'update', 'Delete': 'delete'}

VERBS = ['approve', 'audit', 'sign', 'renew', 'terminate', 'change', 'transfer', 'execute',
         'verify', 'judge', 'assign', 'grant', 'revoke', 'reset', 'issue', 'cancel',
         'pay', 'refund', 'deduct', 'calc', 'dunning', 'handle', 'close', 'read', 'done',
         'record', 'submit', 'roll', 'recalc', 'batch', 'publish', 'status', 'export',
         'import', 'scan', 'sync', 'send', 'broadcast', 'run', 'freeze', 'unfreeze',
         'update', 'delete', 'create', 'view']

ACTION_CN = {
    'view': '查看', 'create': '新建', 'update': '编辑', 'delete': '删除', 'export': '导出',
    'import': '导入', 'audit': '审核', 'approve': '审批', 'sign': '签约', 'renew': '续签',
    'terminate': '终止', 'change': '变更', 'transfer': '换房', 'execute': '执行',
    'status': '状态变更', 'verify': '核验', 'judge': '资格判定', 'assign': '分配',
    'grant': '授权', 'revoke': '撤销', 'reset': '重置', 'issue': '出账', 'cancel': '作废',
    'pay': '核销', 'refund': '退款', 'deduct': '抵扣', 'calc': '计算', 'dunning': '催缴',
    'handle': '处理', 'close': '结单', 'read': '标记已读', 'done': '办结', 'record': '登记',
    'submit': '报送', 'roll': '摇号', 'recalc': '重算', 'batch': '批次管理',
    'publish': '发布', 'scan': '扫描', 'sync': '同步', 'send': '发送', 'run': '执行',
    'freeze': '冻结', 'unfreeze': '解冻', 'broadcast': '广播',
}

RES_CN = {
    'contract': '合同', 'application': '申请', 'termination': '退租', 'exchange': '换房',
    'allocation': '配租', 'waitlist': '轮候', 'contractChange': '合同变更',
    'cohabitant': '同住人', 'publicity': '公示', 'shortRent': '短租',
    'person': '人员', 'profile': '保障档案', 'verify': '实名核验',
    'house': '房源', 'space': '空间', 'device': '设备', 'grant': '授权',
    'keyring': '钥匙', 'access': '门禁记录',
    'bill': '账单', 'payment': '收款', 'deposit': '押金', 'arrear': '催缴',
    'subsidy': '补贴', 'feeItem': '计费项目', 'cashFlow': '资金流水',
    'meterReading': '抄表', 'annualReview': '年审', 'todo': '待办', 'workorder': '工单', 'alert': '告警',
    'complaint': '投诉', 'appeal': '申诉', 'visit': '走访', 'rule': '规则',
    'inspectionPlan': '巡检计划', 'user': '用户', 'role': '角色', 'perm': '权限',
    'org': '组织', 'dict': '数据字典', 'config': '系统参数', 'audit': '审计日志',
    'file': '文件', 'report': '报表', 'app': '开放应用',
}

# ---------- 公开接口白名单 ----------
# 这些接口不放权限注解：认证入口、回调、健康检查、文件上传下载、开放平台回调
PUBLIC_PATTERNS = [
    r'.*/auth/login$', r'.*/auth/logout$', r'.*/auth/me$', r'.*/auth/refresh$',
    r'.*/auth/captcha.*$',
    r'.*/health$', r'.*/version$', r'.*/ping$',
    r'.*/files(/\d+)?(/download)?$', r'.*/files/upload$',
    r'.*/open/(callback|webhook|notify).*$',
    r'.*/payments?/callback.*$',
    r'.*/(dingtalk|wechat)/callback.*$',
]


def is_public(full_path):
    for pat in PUBLIC_PATTERNS:
        if re.match(pat, full_path):
            return True
    return False


def segments(path):
    parts = [p for p in (path or '').split('/') if p]
    if parts and parts[0] == 'api':
        parts = parts[2:]
    return [p for p in parts if not p.startswith('{')]


def derive(controller_path, method_kind, sub_path):
    """返回 (code, module, resource, action)；无法推导时返回 None。"""
    ss = segments(controller_path)
    module = ss[0] if ss else ''
    res = RES_ALIAS.get(ss[1], ss[1]) if len(ss) > 1 else (RES_ALIAS.get(ss[0], ss[0]) if ss else '')
    if not res:
        ssub = segments(sub_path)
        if ssub:
            res = RES_ALIAS.get(ssub[0], ssub[0])
    if module not in MODULES:
        module = RES_MODULE.get(res, module)
    if not module or not res:
        return None
    act = METHOD_ACTION.get(method_kind, 'view')
    low = (sub_path or '').lower()
    for v in VERBS:
        if v in low:
            act = v
            break
    return ('%s:%s:%s' % (module, res, act), module, res, act)


def perm_name(resource, action):
    return '%s-%s' % (RES_CN.get(resource, resource), ACTION_CN.get(action, action))
