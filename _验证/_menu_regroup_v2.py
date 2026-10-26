# -*- coding: utf-8 -*-
"""菜单重构 v2：9 分组 + 命名统一（只改 meta.group / meta.title）。

不动的：路由路径、权限码、组件。
"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
R = os.path.join(ROOT, 'frontend', 'src', 'router', 'index.js')

MAP = {
    '/dashboard': ('工作台', '运营驾驶舱'),
    '/todos': ('工作台', '我的待办'),
    '/messages': ('工作台', '消息中心'),

    '/persons': ('保障与资格', '人员档案'),
    '/applications': ('保障与资格', '申请受理'),
    '/waitlist': ('保障与资格', '轮候管理'),
    '/allocations': ('保障与资格', '配租摇号'),
    '/publicities': ('保障与资格', '公示管理'),
    '/annual-reviews': ('保障与资格', '年审复核'),

    '/contracts': ('合同与租赁', '合同台账'),
    '/contract-changes': ('合同与租赁', '合同变更'),
    '/exchanges': ('合同与租赁', '换房管理'),
    '/terminations': ('合同与租赁', '退租管理'),

    '/bills': ('收费与账务', '账单与缴费'),
    '/arrears': ('收费与账务', '催缴管理'),
    '/deposits': ('收费与账务', '押金与退款'),
    '/subsidies': ('收费与账务', '补贴管理'),
    '/cashflow': ('收费与账务', '资金流水'),
    '/fee-items': ('收费与账务', '计费项目'),

    '/meter-readings': ('计量与能耗', '抄表管理'),
    '/energy': ('计量与能耗', '能耗分析'),

    '/houses': ('房源与空间', '房源台账'),
    '/spaces': ('房源与空间', '空间层级'),
    '/house-calendar': ('房源与空间', '日房态'),
    '/short-rent': ('房源与空间', '短租订单'),

    '/devices': ('设备与通行', '设备管理'),
    '/device-bind': ('设备与通行', '设备绑定'),
    '/dev-events': ('设备与通行', '设备告警'),
    '/access': ('设备与通行', '通行记录'),
    '/keyring': ('设备与通行', '钥匙包'),
    '/grants': ('设备与通行', '授权与对账'),

    '/workorders': ('服务与监督', '工单维保'),
    '/complaints': ('服务与监督', '投诉管理'),
    '/appeals': ('服务与监督', '申诉管理'),
    '/credits': ('服务与监督', '信用惩戒'),
    '/visits': ('服务与监督', '来访登记'),
    '/alerts': ('服务与监督', '告警规则'),

    '/reports': ('系统与数据', '报表导出'),
    '/gov': ('系统与数据', '监管报送'),
    '/orgs': ('系统与数据', '组织机构'),
    '/rbac': ('系统与数据', '用户与权限'),
    '/sys': ('系统与数据', '系统支撑'),
    '/open': ('系统与数据', '开放平台'),
    '/help': ('系统与数据', '使用帮助'),
    '/ops-center': ('系统与数据', '运维操作台'),
    '/ops-extras': ('系统与数据', '扩展操作台'),
}

s = io.open(R, encoding='utf-8').read()
changed = 0
for path, (group, title) in MAP.items():
    pat = re.compile(r"(path: '" + re.escape(path) + r"',[\s\S]{0,400}?meta: \{)([^}]*)(\})")
    m = pat.search(s)
    if not m:
        print('未匹配:', path)
        continue
    meta = m.group(2)
    new_meta = re.sub(r"group: '[^']*'", "group: '%s'" % group, meta)
    new_meta = re.sub(r"title: '[^']*'", "title: '%s'" % title, new_meta)
    s = s[:m.start(2)] + new_meta + s[m.end(2):]
    changed += 1

io.open(R, 'w', encoding='utf-8', newline='').write(s)
print('已更新路由分组/标题:', changed, '/', len(MAP))
