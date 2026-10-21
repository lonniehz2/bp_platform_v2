# -*- coding: utf-8 -*-
"""用括号配平正确插入 personMapper 参数"""
import io
import os
import re

T = r'D:\Work\业务平台开发\backend\src\test\java\com\yundao\bp\biz'
FILES = ['ApplicationQualifyGateTest.java', 'ApplicationModuleTest.java',
         'ApplicationVerifyGateTest.java']


def fix_call(s):
    key = 'new ApplicationServiceImpl('
    i = s.find(key)
    if i < 0:
        return s, False
    j = i + len(key)
    depth = 1
    while j < len(s) and depth > 0:
        if s[j] == '(':
            depth += 1
        elif s[j] == ')':
            depth -= 1
        j += 1
    close = j - 1                      # 指向匹配的 ')'
    inner = s[i + len(key):close]
    if 'personMapper' in inner:
        return s, False
    return s[:close] + ', personMapper' + s[close:], True


for f in FILES:
    p = os.path.join(T, f)
    s = io.open(p, encoding='utf-8').read()
    # 先修掉上一轮插错的位置
    s = s.replace('new SnowflakeIdGenerator(1, 1, personMapper)',
                  'new SnowflakeIdGenerator(1, 1)')
    s, done = fix_call(s)
    if done:
        io.open(p, 'w', encoding='utf-8').write(s)
        print('  ✓ %s' % f)
        m = re.search(r'new ApplicationServiceImpl\([\s\S]{0,220}?\)\s*;', s)
        if m:
            print('     ' + re.sub(r'\s+', ' ', m.group(0))[:200])
    else:
        print('  - %s 无需修改（或已含 personMapper）' % f)
        m = re.search(r'new ApplicationServiceImpl\([\s\S]{0,220}?\)\s*;', s)
        if m:
            print('     ' + re.sub(r'\s+', ' ', m.group(0))[:200])
