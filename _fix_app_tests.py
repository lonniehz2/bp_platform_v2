# -*- coding: utf-8 -*-
"""修正 3 个测试类的构造函数调用（新增 PersonMapper 参数）"""
import io
import os
import re

T = r'D:\Work\业务平台开发\backend\src\test\java\com\yundao\bp\biz'
FILES = ['ApplicationQualifyGateTest.java', 'ApplicationModuleTest.java',
         'ApplicationVerifyGateTest.java']

for f in FILES:
    p = os.path.join(T, f)
    if not os.path.exists(p):
        print('  !! 不存在 %s' % f)
        continue
    s = io.open(p, encoding='utf-8').read()
    if 'personMapper' in s:
        print('  - %s 已处理' % f)
        continue

    # 1) 找到 new ApplicationServiceImpl(...) 调用并补参数
    m = re.search(r'new ApplicationServiceImpl\(([^)]*)\)', s)
    if not m:
        print('  !! %s 未找到构造调用' % f)
        continue
    args = m.group(1)
    s = s.replace(m.group(0),
                  'new ApplicationServiceImpl(%s, personMapper)' % args.strip(), 1)

    # 2) 声明 mock
    decl = '    private PersonMapper personMapper;\n'
    anchor = re.search(r'\n(    @\w+[^\n]*\n)*    private \w+Mapper \w+;', s)
    if anchor:
        s = s[:anchor.start() + 1] + decl + s[anchor.start() + 1:]
    else:
        s = s.replace('class ', 'class ', 1)

    # 3) import
    if 'import com.yundao.bp.person.mapper.PersonMapper;' not in s:
        i = s.find('\nimport ')
        s = s[:i] + '\nimport com.yundao.bp.person.mapper.PersonMapper;' + s[i:]

    io.open(p, 'w', encoding='utf-8').write(s)
    print('  ✓ %s 已补 personMapper' % f)
    print('     构造：%s' % re.search(r'new ApplicationServiceImpl\([^)]*\)', s).group(0)[:120])
