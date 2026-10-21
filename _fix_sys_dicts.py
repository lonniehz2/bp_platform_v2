# -*- coding: utf-8 -*-
"""修 SysAdmin 字典加载：只按 dictType 查询"""
import io
import re

P = r'D:\Work\业务平台开发\frontend\src\views\SysAdmin.vue'
s = io.open(P, encoding='utf-8').read()

# 找到所有 '/sys/dicts' 调用
hits = re.findall(r"[^\n]*'/sys/dicts'[^\n]*", s)
print('当前调用：')
for h in hits[:6]:
    print('   ' + h.strip()[:120])

# 统一改为带类型；并确保 dictType 有默认值
s = s.replace("req.get('/sys/dicts',", "req.get('/sys/dicts/' + dictType.value,")
s = s.replace("req.get('/sys/dicts')", "req.get('/sys/dicts/' + dictType.value)")

if "const dictType = ref(" not in s:
    m = re.search(r'const loading = ref\(false\)', s)
    if m:
        s = s[:m.end()] + "\nconst dictType = ref('HOUSE_TYPE')" + s[m.end():]
        print('  ✓ 补 dictType 默认值')

io.open(P, 'w', encoding='utf-8').write(s)

after = re.findall(r"[^\n]*'/sys/dicts[^\n]*", s)
print('\n修改后：')
for h in after[:6]:
    print('   ' + h.strip()[:120])
