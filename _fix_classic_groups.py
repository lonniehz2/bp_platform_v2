# -*- coding: utf-8 -*-
"""风格1 恢复业务流分组（与风格2 的参考系统分组并存，便于对比）"""
import io
import os

LAY = r'D:\Work\业务平台开发\frontend\src\layout'

# ---------- 1) useMenu.js 增加风格1 的独立分组 ----------
P = os.path.join(LAY, 'useMenu.js')
s = io.open(P, encoding='utf-8').read()

if 'CLASSIC_GROUP' not in s:
    ADD = '''
/**
 * 风格1（宽侧栏）专用分组：按**保障房业务流**划分。
 *
 * 与 meta.group（风格2，参照参考系统的 仪表盘/会员/线索/房源/合同/财务/管理后台/更多）
 * 完全独立，两套并存以便对比两种信息架构。
 */
export const CLASSIC_ORDER = [
  '运营总览', '资格准入', '配租与合同', '账务收费',
  '退出与监督', '资产与设备', '服务与协同', '组织与系统'
]

export const CLASSIC_ICON = {
  运营总览: 'DataBoard',
  资格准入: 'Tickets',
  配租与合同: 'Document',
  账务收费: 'Money',
  退出与监督: 'SwitchButton',
  资产与设备: 'OfficeBuilding',
  服务与协同: 'Service',
  组织与系统: 'Setting'
}

/** 路径 → 风格1 分组 */
const CLASSIC_GROUP = {
  '/dashboard': '运营总览', '/reports': '运营总览',

  '/persons': '资格准入', '/applications': '资格准入',
  '/waitlist': '资格准入', '/publicities': '资格准入',
  '/annual-reviews': '资格准入',

  '/allocations': '配租与合同', '/contracts': '配租与合同',
  '/contract-changes': '配租与合同', '/exchanges': '配租与合同',

  '/fee-items': '账务收费', '/bills': '账务收费', '/deposits': '账务收费',
  '/arrears': '账务收费', '/subsidies': '账务收费', '/cashflow': '账务收费',

  '/terminations': '退出与监督', '/credits': '退出与监督',
  '/appeals': '退出与监督',

  '/houses': '资产与设备', '/spaces': '资产与设备',
  '/house-calendar': '资产与设备', '/short-rent': '资产与设备',
  '/devices': '资产与设备', '/access': '资产与设备',
  '/keyring': '资产与设备', '/grants': '资产与设备',

  '/workorders': '服务与协同', '/alerts': '服务与协同',
  '/complaints': '服务与协同', '/visits': '服务与协同',
  '/messages': '服务与协同',

  '/orgs': '组织与系统', '/rbac': '组织与系统', '/sys': '组织与系统',
  '/ops-center': '组织与系统', '/ops-extras': '组织与系统',
  '/open': '组织与系统', '/gov': '组织与系统'
}
'''
    s = s.replace('export function useMenu() {', ADD + '\nexport function useMenu() {', 1)

    # 在 useMenu 中补充 classicGroups
    s = s.replace('''  function titleOf(path) {''',
                  '''  /** 风格1：按业务流分组 */
  const classicGroups = computed(() => {
    const out = []
    for (const name of CLASSIC_ORDER) {
      const items = menus.value
        .filter((m) => CLASSIC_GROUP[m.path] === name)
        .sort((a, b) => (MENU_RANK[a.path] || 999) - (MENU_RANK[b.path] || 999))
      if (items.length) {
        out.push({ name, icon: CLASSIC_ICON[name] || 'Menu', items })
      }
    }
    return out
  })

  function titleOf(path) {''', 1)

    s = s.replace('return { menus, groups, titleOf, groupOf }',
                  'return { menus, groups, classicGroups, titleOf, groupOf }')
    io.open(P, 'w', encoding='utf-8').write(s)
    print('  ✓ useMenu.js：新增 classicGroups（业务流分组）')

# ---------- 2) LayoutClassic 使用 classicGroups ----------
C = os.path.join(LAY, 'LayoutClassic.vue')
c = io.open(C, encoding='utf-8').read()
c = c.replace('const { groups, titleOf, groupOf } = useMenu()',
              'const { classicGroups: groups, titleOf, groupOf } = useMenu()')
io.open(C, 'w', encoding='utf-8').write(c)
print('  ✓ LayoutClassic.vue 改用业务流分组')

# 校验两套分组
u = io.open(P, encoding='utf-8').read()
print('\n  风格1 分组数：%d' % len(__import__('re').findall(r"^  '[\u4e00-\u9fa5]+': '[^']+'" + '$', u, 8)))
print('  风格2 分组（meta.group）保持参考系统命名')
