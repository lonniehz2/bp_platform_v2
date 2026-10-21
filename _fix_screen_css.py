# -*- coding: utf-8 -*-
"""修复大屏高度塌陷：grid 容器内 flex:1 无效 → 显式声明行高"""
import io

C = r'D:\Work\业务平台开发\frontend\src\screen\screen.css'
s = io.open(C, encoding='utf-8').read()

old_body = '.screen-body { flex: 1; display: grid; grid-template-columns: 1fr; gap: 10px; min-height: 0; }'
new_body = ('.screen-body {\n'
            '  flex: 1;\n'
            '  display: grid;\n'
            '  /* 关键：显式两行，第二行 1fr 才能把剩余高度给图表区；\n'
            '     否则 .charts 的 flex:1 在 grid 中无效，高度塌陷为 0，ECharts 画不出来 */\n'
            '  grid-template-columns: 1fr;\n'
            '  grid-template-rows: auto 1fr;\n'
            '  gap: 10px;\n'
            '  min-height: 0;\n'
            '}')
assert old_body in s, '未找到 .screen-body 原始规则'
s = s.replace(old_body, new_body, 1)

old_charts = '.charts { flex: 1; display: grid; grid-template-columns: 1.1fr 1fr 1fr; gap: 10px; min-height: 0; }'
new_charts = ('.charts {\n'
              '  display: grid;\n'
              '  grid-template-columns: 1.1fr 1fr 1fr;\n'
              '  gap: 10px;\n'
              '  min-height: 0;\n'
              '  height: 100%;\n'
              '}')
if old_charts in s:
    s = s.replace(old_charts, new_charts, 1)

# panel 需要在 grid 里拉伸并允许内部 flex 生效
old_panel = s[s.find('.panel {'):s.find('}', s.find('.panel {')) + 1]
if 'display: flex' not in old_panel:
    s = s.replace('.panel .title',
                  '.panel { display: flex; flex-direction: column; min-height: 0; }\n'
                  '.panel .title', 1)

io.open(C, 'w', encoding='utf-8').write(s)
print('  ✓ screen.css：screen-body 改为 grid-template-rows: auto 1fr')

# 打印最终关键规则
for key in ('.screen-body', '.charts', '.panel {', '.chart {'):
    i = s.find(key)
    if i >= 0:
        j = s.find('}', i) + 1
        print('\n' + s[i:j])
