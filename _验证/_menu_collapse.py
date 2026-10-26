# -*- coding: utf-8 -*-
"""菜单收敛：
1) 隐藏「运维操作台 / 扩展操作台」（与业务页重复）
2) 多页签页面在菜单里只占一项（点进去用页内 tab 切换），
   避免一个页面把菜单撑出 3 项。
"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                 'frontend', 'src', 'layout', 'useMenu.js')
s = io.open(P, encoding='utf-8').read()

# 1) 导入隐藏清单
if 'HIDDEN_PATHS' not in s:
    s = s.replace("  MENU_DESC, MENU_BADGE_KEY, basePathOf\n} from './menuConfig'",
                  "  MENU_DESC, MENU_BADGE_KEY, basePathOf, HIDDEN_PATHS\n} from './menuConfig'")
    print('导入 HIDDEN_PATHS')

# 2) 过滤隐藏路径 + 多页签收敛为父项
OLD = """    for (const m of menuRoutes) {
      const code = m.meta?.perm || pagePermCode(m.path)
      const allowed = !code || auth.has(code)
      if (!allowed && !showDisabled.value) continue

      const basePath = NAME_BASE[m.name] || m.path.split('/:')[0]
      const tabs = TAB_MENU[m.name]
      const desc = MENU_DESC[basePath] || ''

      if (!tabs) {
        out.push({
          path: basePath,
          name: m.name,
          meta: m.meta,
          desc,
          badgeKey: MENU_BADGE_KEY[basePath] || '',
          disabled: !allowed
        })
        continue
      }
      // 有子页签：父项不单独出现，展开为子项（父项无权限则子项全部禁用）
      for (const t of tabs) {
        out.push({
          path: basePath + '/' + t.tab,
          name: m.name + '-' + t.tab,
          meta: { ...m.meta, title: t.title },
          desc: desc,
          badgeKey: MENU_BADGE_KEY[basePath] || '',
          disabled: !allowed,
          _parent: basePath
        })
      }
    }"""

NEW = """    for (const m of menuRoutes) {
      const basePath = NAME_BASE[m.name] || m.path.split('/:')[0]
      // 运维/扩展操作台与业务页重复，菜单不显示（路由仍可直接访问）
      if (HIDDEN_PATHS.includes(basePath)) continue

      const code = m.meta?.perm || pagePermCode(m.path)
      const allowed = !code || auth.has(code)
      if (!allowed && !showDisabled.value) continue

      const tabs = TAB_MENU[m.name]
      const desc = MENU_DESC[basePath] || ''

      // 多页签页面：菜单只占一项，落到默认页签，页内再切换
      const path = tabs && tabs.length ? basePath + '/' + tabs[0].tab : basePath
      out.push({
        path,
        name: m.name,
        meta: m.meta,
        desc,
        badgeKey: MENU_BADGE_KEY[basePath] || '',
        disabled: !allowed,
        _parent: tabs && tabs.length ? basePath : undefined
      })
    }"""

if OLD in s:
    s = s.replace(OLD, NEW, 1)
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('菜单已收敛：隐藏运维台 + 多页签合并为一项')
else:
    print('锚点不匹配，未修改')
