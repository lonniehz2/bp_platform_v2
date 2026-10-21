# -*- coding: utf-8 -*-
"""按 22 字段完整签名修正测试"""
import io
import re

P = (r'D:\Work\业务平台开发\backend\src\test\java\com\yundao\bp\biz'
     r'\ApplicationVerifyGateTest.java')
s = io.open(P, encoding='utf-8').read()

# 用正则替换两个构造调用
def build(commit, agree):
    return ('new ApplicationCreateCmd(1L, personId, "PUBLIC", "HOUSE", "ONLINE", 3,\n'
            '                null, null, null, null, null, null, null, null, null, null,\n'
            '                null, %d, %d, null)' % (commit, agree))

# 1) 正常申请
s = re.sub(r'return new ApplicationCreateCmd\(1L, personId.*?\);',
           'return ' + build(1, 1) + ';', s, count=1, flags=re.S)

# 2) 承诺书未签
s = re.sub(r'ApplicationCreateCmd bad = new ApplicationCreateCmd\(1L, 4001L.*?\);',
           'ApplicationCreateCmd bad =\n                new ApplicationCreateCmd(1L, 4001L, "PUBLIC", "HOUSE", "ONLINE", 3,\n'
           '                        null, null, null, null, null, null, null, null, null,\n'
           '                        null, null, 0, 0, null);', s, count=1, flags=re.S)

io.open(P, 'w', encoding='utf-8').write(s)

# 校验字段数
n = s.count('new ApplicationCreateCmd(')
print('构造调用 %d 处（应为 2）' % n)
m = re.search(r'private static ApplicationCreateCmd cmd.*?\n    \}', s, re.S)
print()
print('cmd 方法当前内容：')
print(m.group(0) if m else '未找到')
