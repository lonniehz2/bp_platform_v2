# -*- coding: utf-8 -*-
"""帮助深链：Help 页支持 ?sec=，布局顶部问号带上当前页章节。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
V = os.path.join(ROOT, 'frontend', 'src', 'views', 'Help.vue')
L = os.path.join(ROOT, 'frontend', 'src', 'layout')

# ---------- Help.vue ----------
s = io.open(V, encoding='utf-8').read()
if 'route.query.sec' not in s:
    s = s.replace(
        "import { computed, ref } from 'vue'\nimport { HELP_SECTIONS, HELP_VERSION } from '@/content/help'",
        "import { computed, onMounted, ref } from 'vue'\n"
        "import { useRoute } from 'vue-router'\n"
        "import { HELP_SECTIONS, HELP_VERSION } from '@/content/help'\n\n"
        "const route = useRoute()")
    s = s.replace(
        "const keyword = ref('')\nconst active = ref(HELP_SECTIONS[0]?.id || '')",
        "const keyword = ref('')\n"
        "const sec0 = String(route.query.sec || '')\n"
        "const active = ref(HELP_SECTIONS.some((x) => x.id === sec0)\n"
        "  ? sec0 : (HELP_SECTIONS[0]?.id || ''))\n\n"
        "// 顶部问号会带 ?sec=xxx：进入后自动滚到对应章节\n"
        "onMounted(() => {\n"
        "  if (sec0) setTimeout(() => jump(sec0), 120)\n"
        "})")
    io.open(V, 'w', encoding='utf-8', newline='').write(s)
    print('Help.vue 已支持 ?sec= 定位')

# ---------- 两个布局 ----------
OLD_FN = """function toHelp() {
  router.push('/help')
}"""
NEW_FN = """function toHelp() {
  // 带当前页对应的帮助章节，省去用户在大纲里找
  router.push({ path: '/help', query: { sec: sectionForRoute(route.path) } })
}"""

for fn in ('LayoutRail.vue', 'LayoutClassic.vue'):
    p = os.path.join(L, fn)
    t = io.open(p, encoding='utf-8').read()
    if 'sectionForRoute' in t:
        print(fn, '已改')
        continue
    if OLD_FN not in t:
        print(fn, '未找到 toHelp')
        continue
    t = t.replace(OLD_FN, NEW_FN, 1)
    t = t.replace("import StyleSwitch from './StyleSwitch.vue'",
                  "import StyleSwitch from './StyleSwitch.vue'\n"
                  "import { sectionForRoute } from '@/content/help'", 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(t)
    print(fn, 'toHelp 已带章节')
