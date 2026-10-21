# -*- coding: utf-8 -*-
"""修复①：为路由加 meta.group，Layout 改为分组二级菜单"""
import io
import re

R = r'D:\Work\业务平台开发\frontend\src\router\index.js'
s = io.open(R, encoding='utf-8').read()

GROUP = {
    'dashboard': '运营监控', 'reports': '运营监控', 'screen': '运营监控',
    'applications': '申请与配租', 'waitlist': '申请与配租',
    'allocations': '申请与配租', 'publicities': '申请与配租',
    'annual-reviews': '申请与配租',
    'contracts': '合同与财务', 'contract-changes': '合同与财务',
    'bills': '合同与财务', 'deposits': '合同与财务', 'arrears': '合同与财务',
    'cashflow': '合同与财务', 'fee-items': '合同与财务',
    'subsidies': '合同与财务', 'terminations': '合同与财务',
    'orgs': '资产与设备', 'spaces': '资产与设备', 'houses': '资产与设备',
    'devices': '资产与设备', 'access': '资产与设备',
    'house-calendar': '资产与设备', 'keyring': '资产与设备',
    'grants': '资产与设备',
    'persons': '人员与服务', 'workorders': '人员与服务', 'alerts': '人员与服务',
    'complaints': '人员与服务', 'visits': '人员与服务',
    'appeals': '人员与服务', 'credits': '人员与服务',
    'exchanges': '人员与服务', 'short-rent': '人员与服务',
    'messages': '人员与服务',
    'rbac': '系统与集成', 'sys': '系统与集成', 'open': '系统与集成',
    'gov': '系统与集成', 'ops-center': '系统与集成',
}

# 给每条路由的 meta 加 group（若尚未有）
added = 0
for m in re.finditer(r"path:\s*'/([a-z\-]+)',([\s\S]{0,420}?)meta:\s*\{([^}]*)\}", s):
    path, mid, meta = m.group(1), m.group(2), m.group(3)
    if path not in GROUP or 'group:' in meta:
        continue
    new_meta = meta.rstrip() + ", group: '%s' " % GROUP[path]
    old = "meta: {%s}" % meta
    new = "meta: {%s}" % new_meta
    s = s.replace(old, new, 1)
    added += 1

io.open(R, 'w', encoding='utf-8').write(s)
print('  ✓ 已为 %d 条路由加 meta.group' % added)

# ---------- Layout：分组渲染 ----------
L = r'D:\Work\业务平台开发\frontend\src\layout\Layout.vue'
lay = io.open(L, encoding='utf-8').read()

old_menu = re.search(r'<el-menu[\s\S]*?</el-menu>', lay)
assert old_menu, 'el-menu 未找到'

NEW_MENU = '''<el-menu
        :default-active="$route.path"
        :collapse="collapsed"
        :collapse-transition="false"
        background-color="#1f2d3d"
        text-color="#c0c4cc"
        active-text-color="#409eff"
        router
      >
        <template v-for="g in groupedMenus" :key="g.name">
          <el-sub-menu v-if="g.items.length > 1" :index="g.name">
            <template #title>
              <el-icon><component :is="g.icon" /></el-icon>
              <span>{{ g.name }}</span>
            </template>
            <el-menu-item v-for="m in g.items" :key="m.path" :index="m.path">
              <el-icon><component :is="m.meta.icon" /></el-icon>
              <template #title>{{ m.meta.title }}</template>
            </el-menu-item>
          </el-sub-menu>
          <el-menu-item v-else :index="g.items[0].path">
            <el-icon><component :is="g.items[0].meta.icon" /></el-icon>
            <template #title>{{ g.items[0].meta.title }}</template>
          </el-menu-item>
        </template>
      </el-menu>'''

lay = lay[:old_menu.start()] + NEW_MENU + lay[old_menu.end():]

# 分组顺序与图标
GROUP_META = """const GROUP_ORDER = ['运营监控', '申请与配租', '合同与财务', '资产与设备',
                     '人员与服务', '系统与集成']
const GROUP_ICON = {
  运营监控: 'DataBoard', 申请与配租: 'Tickets', 合同与财务: 'Money',
  资产与设备: 'OfficeBuilding', 人员与服务: 'UserFilled', 系统与集成: 'Setting'
}
"""

lay = lay.replace(
    "const menus = computed(() =>\n  menuRoutes.filter((m) => !m.meta?.perm || auth.has(m.meta.perm))\n)",
    GROUP_META + """
const menus = computed(() =>
  menuRoutes.filter((m) => !m.meta?.perm || auth.has(m.meta.perm))
)

/** 按 meta.group 分组，固定顺序输出 */
const groupedMenus = computed(() => {
  const out = []
  for (const name of GROUP_ORDER) {
    const items = menus.value.filter((m) => (m.meta?.group || '其他') === name)
    if (items.length) out.push({ name, icon: GROUP_ICON[name] || 'Menu', items })
  }
  const rest = menus.value.filter((m) => !GROUP_ORDER.includes(m.meta?.group || '其他'))
  if (rest.length) out.push({ name: '其他', icon: 'Menu', items: rest })
  return out
})
""", 1)

io.open(L, 'w', encoding='utf-8').write(lay)
print('  ✓ Layout.vue 改为分组二级菜单（%d 组）' % len(GROUP))
