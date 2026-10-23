# -*- coding: utf-8 -*-
"""在三个脚本的 main() 之前插入映射补充（alias/module/控制器兜底）。"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))

BLOCK = '''
# ---------- 映射补充（资源别名 / 模块归属 / 控制器兜底） ----------
RES_ALIAS.update({
    'alerts': 'alert', 'rules': 'rule', 'grants': 'grant', 'grant-reconcile': 'grant',
    'guarantee-profiles': 'profile', 'access-records': 'access',
    'house-calendar': 'house', 'files': 'file', 'todos': 'todo',
    'publicities': 'publicity', 'verify-records': 'verify', 'visits': 'visit',
    'short-rent-orders': 'shortRent', 'meter-readings': 'meterReading',
    'inspection-plans': 'inspectionPlan', 'cohabitants': 'cohabitant',
    'applications': 'application', 'terminations': 'termination',
    'houses': 'house', 'spaces': 'space', 'persons': 'person', 'users': 'user',
    'roles': 'role', 'orgs': 'org', 'bills': 'bill', 'payments': 'payment',
    'deposits': 'deposit', 'subsidies': 'subsidy', 'workorders': 'workorder',
    'complaints': 'complaint', 'appeals': 'appeal', 'permissions': 'perm',
})
RES_MODULE.update({
    'alert': 'ops', 'rule': 'ops', 'grant': 'asset', 'profile': 'person',
    'access': 'asset', 'file': 'sys', 'publicity': 'biz', 'verify': 'person',
    'visit': 'ops', 'shortRent': 'biz', 'meterReading': 'fin',
    'inspectionPlan': 'ops', 'cohabitant': 'biz', 'org': 'iam',
    'open': 'open', 'gov': 'gov', 'contractChange': 'biz',
})
CONTROLLER_FALLBACK = {
    'ContractChangeController': ('contractChange', 'biz'),
    'PublicityReviewController': ('publicity', 'biz'),
    'VerifyRecordController': ('verify', 'person'),
    'VisitController': ('visit', 'ops'),
    'OpenPlatformController': ('app', 'open'),
    'GovReportController': ('report', 'gov'),
}


def fallback_target(fn_name):
    """类级路径不足时，按控制器文件名兜底。"""
    return CONTROLLER_FALLBACK.get(fn_name.replace('.java', ''))


'''

for fn in ('_add_require_perm.py', '_gen_endpoint_perms.py', '_audit_perm_offline.py'):
    p = os.path.join(HERE, fn)
    if not os.path.exists(p):
        print('%s 不存在' % fn)
        continue
    s = io.open(p, encoding='utf-8').read()
    if 'CONTROLLER_FALLBACK' in s:
        print('%s 已含补充块' % fn)
        continue
    s = s.replace('def main():', BLOCK + '\ndef main():', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('%s：已插入补充块' % fn)
