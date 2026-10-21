# -*- coding: utf-8 -*-
"""修编译错误：重复 @Override；TerminationServiceImpl 被误改"""
import io
import re

J = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'

# ---------- 1) PersonServiceImpl：删除重复的 @Override ----------
P = J + r'\person\service\impl\PersonServiceImpl.java'
s = io.open(P, encoding='utf-8').read()
s = s.replace('''    @Override
    @Transactional(rollbackFor = Exception.class)
    @Override
    public PersonVO update(''', '''    @Override
    @Transactional(rollbackFor = Exception.class)
    public PersonVO update(''')
io.open(P, 'w', encoding='utf-8').write(s)
print('  ✓ PersonServiceImpl 去掉重复 @Override')

# ---------- 2) TerminationServiceImpl：检查是否被插入 update ----------
T = J + r'\biz\service\impl\TerminationServiceImpl.java'
t = io.open(T, encoding='utf-8').read()
if 'PersonUpdateCmd' in t:
    # 把误插的整段删掉
    m = re.search(r'    @Override\s*\n(    @Transactional[^\n]*\n)?'
                  r'    public [\w<>, ]+ update\([^)]*PersonUpdateCmd[^)]*\)\s*\{'
                  r'[\s\S]*?\n    \}\n\n', t)
    if m:
        t = t[:m.start()] + t[m.end():]
        io.open(T, 'w', encoding='utf-8').write(t)
        print('  ✓ TerminationServiceImpl 删除误插的 update 方法')
    else:
        print('  ! 未匹配到误插代码，手工检查')
        for i, ln in enumerate(t.split('\n'), 1):
            if 'PersonUpdateCmd' in ln or ('update(' in ln and 'public' in ln):
                print('    %d: %s' % (i, ln.strip()[:90]))
else:
    print('  - TerminationServiceImpl 未被污染')

# 校验
t2 = io.open(T, encoding='utf-8').read()
print('  残留 PersonUpdateCmd: %d' % t2.count('PersonUpdateCmd'))
