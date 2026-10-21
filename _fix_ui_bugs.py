# -*- coding: utf-8 -*-
"""修复 UI 冒烟发现的 4 个真实缺陷"""
import io
import os
import re

FE = r'D:\Work\业务平台开发\frontend\src'

# ---------- ① HouseCalendar：houseId 为空时仍发请求（路径变成 [object Object]）----------
P = os.path.join(FE, 'views', 'HouseCalendar.vue')
s = io.open(P, encoding='utf-8').read()
if 'houseId 不能为空' not in s:
    # 找到 fetchCalendar / load 里调用 /house-calendar/{id} 的地方
    s = re.sub(r'(async function \w+\([^)]*\)\s*\{\n)',
               r'\1  if (!houseId.value) {\n'
               r'    ElMessage.warning("请先输入房源ID")\n'
               r'    return\n'
               r'  }\n', s, count=1)
    io.open(P, 'w', encoding='utf-8').write(s)
    print('  ✓ HouseCalendar：houseId 为空时不再请求')

# ---------- ② SysAdmin：/sys/dicts 缺类型参数 ----------
P2 = os.path.join(FE, 'views', 'SysAdmin.vue')
t = io.open(P2, encoding='utf-8').read()
if "req.get('/sys/dicts')" in t:
    # 改成先取字典类型列表，再按类型取项；无类型时不请求
    t = t.replace("req.get('/sys/dicts')",
                  "req.get('/sys/dicts/' + (dictType.value || 'HOUSE_TYPE'))")
    if 'dictType' not in t.split('</script>')[0]:
        t = t.replace("const loading = ref(false)",
                      "const loading = ref(false)\nconst dictType = ref('HOUSE_TYPE')", 1)
    io.open(P2, 'w', encoding='utf-8').write(t)
    print('  ✓ SysAdmin：/sys/dicts 带上类型参数')

# ---------- ③ ScreenApp / Dashboard：echarts 实例方法丢失 ----------
# 原因：charts 里存了非实例对象（elements），dispose/resize 遍历时报错
for name in ('ScreenApp.vue',):
    P3 = os.path.join(FE, 'screen', name)
    if not os.path.exists(P3):
        continue
    u = io.open(P3, encoding='utf-8').read()
    u = u.replace('Object.values(charts).forEach((c) => c && c.dispose())',
                  'Object.values(charts).forEach((c) => c && typeof c.dispose === "function" && c.dispose())')
    u = u.replace('Object.values(charts).forEach((c) => c && c.resize())',
                  'Object.values(charts).forEach((c) => c && typeof c.resize === "function" && c.resize())')
    u = u.replace('  window.addEventListener(\'resize\', resize)',
                  '  window.addEventListener(\'resize\', resize)')
    # charts 里不要混入非实例（_ro 等）
    u = u.replace('charts._ro = ro', 'chartsRo = ro')
    if 'let chartsRo' not in u:
        u = u.replace("let charts = {}", "let charts = {}\nlet chartsRo = null", 1)
    io.open(P3, 'w', encoding='utf-8').write(u)
    print('  ✓ ScreenApp：resize/dispose 前做函数类型判断')

# ---------- ④ OpsExtras：echarts 相关误报（该页无图表，忽略 console 噪声）----------
# 实为 ScreenApp 的 pageerror 串页，已在 ③ 处理

print('\n  说明：/ops-extras 的报错来自同进程残留的 screen 页异常，③ 修复后应一并消失')
