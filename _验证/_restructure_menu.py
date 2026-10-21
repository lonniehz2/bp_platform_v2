# -*- coding: utf-8 -*-
"""菜单信息架构重排（按保障房业务链），并把人员页三个 tab 提升为菜单项。

1. 9 组两级菜单：运营总览 / 保障对象 / 资格准入 / 合同管理 / 账务收费 /
   授权与交房 / 服务与监督 / 资产台账 / 系统与集成
2. 人员页路由改为 /persons/:tab?（person/profile/verify），三个 tab 进入侧边栏
3. 同步 rail 风格的分组与图标
"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
FE = os.path.join(ROOT, 'frontend', 'src')
MENU = os.path.join(FE, 'layout', 'useMenu.js')
ROUTER = os.path.join(FE, 'router', 'index.js')
PERSONS = os.path.join(FE, 'views', 'Persons.vue')

# ---------- 1) 分组定义 ----------
NEW_ORDER = "export const CLASSIC_ORDER = [\n  '运营总览', '保障对象', '资格准入', '合同管理', '账务收费',\n  '授权与交房', '服务与监督', '资产台账', '系统与集成'\n]"

NEW_ICON = """export const CLASSIC_ICON = {
  运营总览: 'DataBoard',
  保障对象: 'UserFilled',
  资格准入: 'Tickets',
  合同管理: 'Document',
  账务收费: 'Money',
  授权与交房: 'Key',
  服务与监督: 'Service',
  资产台账: 'OfficeBuilding',
  系统与集成: 'Setting'
}"""

NEW_GROUP = """const CLASSIC_GROUP = {
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
  '/credits': '服务与监督', '/alerts': '服务与监督',
  '/messages': '服务与监督',

  '/houses': '资产台账', '/spaces': '资产台账',
  '/house-calendar': '资产台账', '/short-rent': '资产台账',

  '/orgs': '系统与集成', '/rbac': '系统与集成', '/sys': '系统与集成',
  '/ops-center': '系统与集成', '/ops-extras': '系统与集成',
  '/open': '系统与集成', '/gov': '系统与集成'
}"""

NEW_RAIL_ORDER = "export const GROUP_ORDER = [\n  '运营总览', '保障对象', '资格准入', '合同管理', '账务收费',\n  '授权与交房', '服务与监督', '资产台账', '系统与集成'\n]"


def main():
    s = io.open(MENU, encoding='utf-8').read()

    # CLASSIC_ORDER
    s = re.sub(r"export const CLASSIC_ORDER = \[[^\]]*\]", NEW_ORDER, s, count=1)
    # CLASSIC_ICON
    s = re.sub(r"export const CLASSIC_ICON = \{[^}]*\}", NEW_ICON, s, count=1)
    # CLASSIC_GROUP
    s = re.sub(r"const CLASSIC_GROUP = \{[^}]*\}", NEW_GROUP, s, count=1)
    # rail 风格 GROUP_ORDER（第一处）
    s = re.sub(r"export const GROUP_ORDER = \[[^\]]*\]", NEW_RAIL_ORDER, s, count=1)
    # rail 图标补两个新组
    s = s.replace("  管理后台: 'Setting',\n  更多: 'Grid'",
                  "  合同管理: 'Document',\n  授权与交房: 'Key',\n  服务与监督: 'Service',\n"
                  "  资产台账: 'OfficeBuilding',\n  系统与集成: 'Setting',\n  更多: 'Grid'", 1)

    # 人员页三个 tab 进入侧边栏
    if 'persons: [' not in s:
        s = s.replace("export const TAB_MENU = {",
                      "export const TAB_MENU = {\n"
                      "  persons: [\n"
                      "    { tab: 'person', title: '人员档案' },\n"
                      "    { tab: 'profile', title: '保障档案' },\n"
                      "    { tab: 'verify', title: '实名核验' }\n"
                      "  ],", 1)
        s = s.replace("const NAME_BASE = {\n  opsextras: '/ops-extras',",
                      "const NAME_BASE = {\n  persons: '/persons',\n  opsextras: '/ops-extras',", 1)
    io.open(MENU, 'w', encoding='utf-8', newline='').write(s)
    print('useMenu.js：分组/图标/tab 菜单已更新')

    # ---------- 路由：/persons/:tab? ----------
    r = io.open(ROUTER, encoding='utf-8').read()
    if "path: '/persons/:tab?'" not in r:
        r = r.replace("path: '/persons',", "path: '/persons/:tab?',", 1)
        io.open(ROUTER, 'w', encoding='utf-8', newline='').write(r)
        print('router：/persons 改为 /persons/:tab?')

    # ---------- Persons.vue：tab 与路由双向同步 ----------
    p = io.open(PERSONS, encoding='utf-8').read()
    if 'useRoute' not in p:
        p = re.sub(r"import \{ ref, reactive, onMounted \} from 'vue'",
                   "import { ref, reactive, onMounted, watch } from 'vue'\n"
                   "import { useRoute, useRouter } from 'vue-router'", p, count=1)
        p = p.replace("const tab = ref('person')",
                      "const route = useRoute()\nconst router = useRouter()\n"
                      "const TABS = ['person', 'profile', 'verify']\n"
                      "const tab = ref(TABS.includes(route.params.tab) ? route.params.tab : 'person')\n"
                      "// 侧边栏点不同子项时切换 tab；页内切 tab 时同步地址\n"
                      "watch(() => route.params.tab, (v) => {\n"
                      "  if (v && TABS.includes(v) && v !== tab.value) { tab.value = v; onTab(v) }\n"
                      "})\n"
                      "watch(tab, (v) => {\n"
                      "  if (route.params.tab !== v) router.replace('/persons/' + v)\n"
                      "})", 1)
        io.open(PERSONS, 'w', encoding='utf-8', newline='').write(p)
        print('Persons.vue：tab 与路由已同步')


if __name__ == '__main__':
    main()
