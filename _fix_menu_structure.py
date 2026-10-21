# -*- coding: utf-8 -*-
"""按业务流程重构左侧菜单分组"""
import io
import re

R = r'D:\Work\业务平台开发\frontend\src\router\index.js'
s = io.open(R, encoding='utf-8').read()

# 业务主线：资格准入 → 配租签约 → 账务收费 → 退出监督
# 资产与设备是支撑底座；服务与协同是运营日常；组织与系统是管理后台
GROUP = {
    # ① 运营总览
    'dashboard': '运营总览', 'reports': '运营总览', 'screen': '运营总览',
    # ② 资格准入（保障对象从建档到获得资格）
    'persons': '资格准入', 'applications': '资格准入', 'waitlist': '资格准入',
    'annual-reviews': '资格准入', 'publicities': '资格准入',
    # ③ 配租与合同（拿到房、签下约）
    'allocations': '配租与合同', 'contracts': '配租与合同',
    'contract-changes': '配租与合同', 'exchanges': '配租与合同',
    # ④ 账务收费（住进来之后的钱）
    'bills': '账务收费', 'deposits': '账务收费', 'arrears': '账务收费',
    'subsidies': '账务收费', 'cashflow': '账务收费', 'fee-items': '账务收费',
    # ⑤ 退出与监督（退租 + 违约救济）
    'terminations': '退出与监督', 'appeals': '退出与监督',
    'credits': '退出与监督',
    # ⑥ 资产与设备（底层资源与门禁）
    'houses': '资产与设备', 'spaces': '资产与设备',
    'house-calendar': '资产与设备', 'short-rent': '资产与设备',
    'devices': '资产与设备', 'access': '资产与设备',
    'keyring': '资产与设备', 'grants': '资产与设备',
    # ⑦ 服务与协同（日常运营）
    'workorders': '服务与协同', 'alerts': '服务与协同',
    'complaints': '服务与协同', 'visits': '服务与协同',
    'messages': '服务与协同',
    # ⑧ 组织与系统（管理后台）
    'orgs': '组织与系统', 'rbac': '组织与系统', 'gov': '组织与系统',
    'open': '组织与系统', 'sys': '组织与系统', 'ops-center': '组织与系统',
}

changed = 0
for path, grp in GROUP.items():
    pat = re.compile(r"(path:\s*'/%s',[\s\S]{0,400}?meta:\s*\{[^}]*?)group:\s*'[^']*'"
                     % re.escape(path))
    m = pat.search(s)
    if m:
        if re.search(r"group:\s*'[^']*'", m.group(0)):
            old = re.search(r"group:\s*'([^']*)'", m.group(0)).group(1)
            if old != grp:
                s = s[:m.start()] + m.group(0).replace(
                    "group: '%s'" % old, "group: '%s'" % grp) + s[m.end():]
                changed += 1
                print('   %-18s %s → %s' % (path, old, grp))
    else:
        print('   !! 未匹配 /%s' % path)

io.open(R, 'w', encoding='utf-8').write(s)
print('\n  ✓ 调整 %d 条路由的分组' % changed)

# ---------- Layout：分组顺序与图标 ----------
L = r'D:\Work\业务平台开发\frontend\src\layout\Layout.vue'
lay = io.open(L, encoding='utf-8').read()

old_block = re.search(r"const GROUP_ORDER = \[[\s\S]*?\n\}", lay)
new_block = '''const GROUP_ORDER = [
  '运营总览', '资格准入', '配租与合同', '账务收费',
  '退出与监督', '资产与设备', '服务与协同', '组织与系统'
]
const GROUP_ICON = {
  运营总览: 'DataBoard',
  资格准入: 'Tickets',
  配租与合同: 'Document',
  账务收费: 'Money',
  退出与监督: 'SwitchButton',
  资产与设备: 'OfficeBuilding',
  服务与协同: 'Service',
  组织与系统: 'Setting'
}'''
if old_block:
    lay = lay[:old_block.start()] + new_block + lay[old_block.end():]
    io.open(L, 'w', encoding='utf-8').write(lay)
    print('  ✓ Layout：分组顺序与图标已更新（8 组）')
