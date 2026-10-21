# -*- coding: utf-8 -*-
"""把 Rbac / SysAdmin / OpsCenter 的 tab 改成路由驱动（与 OpsExtras 一致）

每个页面只需要：
  1. 补 watch + useRoute/useRouter 的导入
  2. tab 初始值取 route.params.tab（非法值回落默认）
  3. tab ↔ 路由双向同步
"""
import io
import os

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'src')

PAGES = [
    ('views/Rbac.vue', 'rbac', ['user', 'role', 'perm'], 'user'),
    ('views/SysAdmin.vue', 'sys', ['audit', 'dict', 'config'], 'audit'),
    ('views/OpsCenter.vue', 'ops-center', ['person', 'house', 'order'], 'person'),
]

IMPORT_A = "import { ref, reactive, onMounted } from 'vue'"
IMPORT_A_NEW = ("import { ref, reactive, onMounted, watch } from 'vue'\n"
                "import { useRoute, useRouter } from 'vue-router'")
IMPORT_B = "import { ref, onMounted } from 'vue'"
IMPORT_B_NEW = ("import { ref, onMounted, watch } from 'vue'\n"
                "import { useRoute, useRouter } from 'vue-router'")


def block(tabs, default, prefix):
    return (
        "const TABS = %r\n"
        "const route = useRoute()\n"
        "const router = useRouter()\n"
        "const tab = ref(TABS.includes(route.params.tab) ? route.params.tab : '%s')\n"
        "watch(() => route.params.tab, (v) => {\n"
        "  const t = TABS.includes(v) ? v : '%s'\n"
        "  if (t !== tab.value) tab.value = t\n"
        "})\n"
        "watch(tab, (v) => {\n"
        "  if (route.params.tab !== v) router.replace('%s/' + v)\n"
        "})"
    ) % (tabs, default, default, '/' + prefix)


def main():
    for rel, prefix, tabs, default in PAGES:
        path = os.path.join(BASE, rel)
        s = io.open(path, encoding='utf-8').read()
        if 'TABS.includes' in s:
            print('%-22s 已改造，跳过' % rel)
            continue
        if IMPORT_A in s:
            s = s.replace(IMPORT_A, IMPORT_A_NEW, 1)
        elif IMPORT_B in s:
            s = s.replace(IMPORT_B, IMPORT_B_NEW, 1)
        else:
            print('%-22s 未找到 import 锚点' % rel)
            continue
        old = "const tab = ref('%s')" % default
        if old not in s:
            print('%-22s 未找到 tab 初始化' % rel)
            continue
        s = s.replace(old, block(tabs, default, prefix), 1)
        io.open(path, 'w', encoding='utf-8', newline='').write(s)
        print('%-22s 已改造 tabs=%s default=%s' % (rel, tabs, default))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
