# -*- coding: utf-8 -*-
"""页面权限按左侧菜单结构呈现（分组 → 菜单项），不再平铺。"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'frontend', 'src', 'views', 'Rbac.vue')

# 模板：页面权限改为按菜单分组渲染
TPL_OLD = re.compile(
    r'          <el-scrollbar max-height="330px">\n'
    r'            <div class="perm-group">\n'
    r'              <div class="perm-group-body">\n'
    r'                <el-checkbox\n'
    r'                  v-for="p in pagePerms"[\s\S]*?\n'
    r'              </div>\n'
    r'            </div>\n'
    r'          </el-scrollbar>')

TPL_NEW = '''          <el-scrollbar max-height="330px">
            <div v-for="mg in pageMenuGroups" :key="mg.group" class="perm-group">
              <div class="perm-group-head">
                <el-checkbox
                  :model-value="mg.items.every((p) => checkedPerms.includes(String(p.id)))"
                  :indeterminate="!mg.items.every((p) => checkedPerms.includes(String(p.id)))
                    && mg.items.some((p) => checkedPerms.includes(String(p.id)))"
                  @change="(v) => toggleGroup(mg, v)">
                  {{ mg.group }}（{{ mg.items.length }}）
                </el-checkbox>
              </div>
              <div class="perm-actions">
                <el-checkbox
                  v-for="p in mg.items" :key="p.id"
                  :model-value="checkedPerms.includes(String(p.id))"
                  :label="p.permName"
                  :title="p.routePath || p.permCode"
                  @change="(v) => togglePerm(p, v)" />
              </div>
            </div>
          </el-scrollbar>'''

# 计算属性：按菜单分组
CALC_ADD = '''
/** 页面权限按左侧菜单分组呈现（分组名与侧边栏一致） */
const pageMenuGroups = computed(() => {
  const order = ['运营总览', '保障对象', '资格准入', '合同管理', '账务收费',
    '授权与交房', '服务与监督', '资产台账', '系统与集成', '其他']
  const map = new Map()
  for (const p of pagePerms.value) {
    const g = menuGroupOf(p.routePath)
    if (!map.has(g)) map.set(g, [])
    map.get(g).push(p)
  }
  return order.filter((g) => map.has(g))
    .map((g) => ({ group: g, key: g, items: map.get(g) }))
})

/** 路由 → 菜单分组（与 useMenu 的 CLASSIC_GROUP 保持一致） */
function menuGroupOf(path) {
  const p = String(path || '')
  const G = {
    '/dashboard': '运营总览', '/reports': '运营总览', '/todos': '运营总览',
    '/persons': '保障对象', '/annual-reviews': '保障对象',
    '/applications': '资格准入', '/waitlist': '资格准入',
    '/allocations': '资格准入', '/publicities': '资格准入',
    '/contracts': '合同管理', '/contract-changes': '合同管理',
    '/exchanges': '合同管理', '/terminations': '合同管理',
    '/fee-items': '账务收费', '/bills': '账务收费', '/deposits': '账务收费',
    '/arrears': '账务收费', '/subsidies': '账务收费', '/cashflow': '账务收费',
    '/devices': '授权与交房', '/access': '授权与交房',
    '/keyring': '授权与交房', '/grants': '授权与交房',
    '/workorders': '服务与监督', '/complaints': '服务与监督',
    '/appeals': '服务与监督', '/visits': '服务与监督',
    '/credits': '服务与监督', '/alerts': '服务与监督', '/messages': '服务与监督',
    '/houses': '资产台账', '/spaces': '资产台账',
    '/house-calendar': '资产台账', '/short-rent': '资产台账',
    '/orgs': '系统与集成', '/rbac': '系统与集成', '/sys': '系统与集成',
    '/ops-center': '系统与集成', '/ops-extras': '系统与集成',
    '/open': '系统与集成', '/gov': '系统与集成'
  }
  return G[p] || '其他'
}
'''


def main():
    s = io.open(P, encoding='utf-8').read()
    m = TPL_OLD.search(s)
    if not m:
        print('模板未匹配，跳过（需人工核对）')
        return 1
    s = s[:m.start()] + TPL_NEW + s[m.end():]
    if 'pageMenuGroups' not in s:
        s = s.replace('const permGroups = computed(() => {', CALC_ADD + '\nconst permGroups = computed(() => {', 1)
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('页面权限已按菜单分组呈现')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
