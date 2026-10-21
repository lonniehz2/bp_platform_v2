# -*- coding: utf-8 -*-
"""修正 _check_pages.py：模板字符串路径 + 通过 api 模块识别写操作"""
import io
import re

P = r'D:\Work\业务平台开发\_验证\_check_pages.py'
s = io.open(P, encoding='utf-8').read()

# 1) 调用提取：允许 ${...}，并归一化为 {}
s = s.replace(
    r'''        for m in re.finditer(r"req\.(get|post|put|delete)\(\s*[`'\"](/[^`'\"$]*)", s):
            path = m.group(2)
            if not path.startswith('/api/'):
                path = '/api/v1' + path
            calls.add((norm(path), m.group(1).upper()))''',
    r'''        for m in re.finditer(r"req\.(get|post|put|delete)\(\s*[`'\"]([^`'\"]*)", s):
            path = m.group(2)
            if not path.startswith('/api/'):
                path = '/api/v1' + path
            calls.add((norm(path), m.group(1).upper()))''')

s = s.replace(
    r'''    for m in re.finditer(r"req\.(get|post|put|delete)\(\s*[`'\"](/[^`'\"$]*)", s):
        path = m.group(2)
        if not path.startswith('/api/'):
            path = '/api/v1' + path
        if (norm(path), m.group(1).upper()) not in backend:''',
    r'''    for m in re.finditer(r"req\.(get|post|put|delete)\(\s*[`'\"]([^`'\"]*)", s):
        path = m.group(2)
        if not path.startswith('/api/'):
            path = '/api/v1' + path
        if (norm(path), m.group(1).upper()) not in backend:''')

# 2) 写操作统计：解析 modules.js 的 api → 方法 → HTTP 动词
s = s.replace("# ---------- 每页调用与写操作 ----------",
              '''# ---------- api 模块：方法 → 动词 ----------
api_verbs = {}
_mtext = io.open(os.path.join(SRC, 'api', 'modules.js'), encoding='utf-8').read()
for m in re.finditer(r'export const (\\w+Api)\\s*=\\s*\\{(.*?)\\n\\}', _mtext, re.S):
    name, body = m.group(1), m.group(2)
    methods = {}
    for mm in re.finditer(r'(\\w+):\\s*\\([^)]*\\)\\s*=>\\s*req\\.(get|post|put|delete)', body):
        methods[mm.group(1)] = mm.group(2).upper()
    api_verbs[name] = methods

# ---------- 每页调用与写操作 ----------''')

s = s.replace('''        # api 模块里的调用也算
        writes = {c for c in calls if c[1] != 'GET'}''',
              '''        writes = {c for c in calls if c[1] != 'GET'}
        # 通过 api 模块封装的写操作（req.* 只在 modules.js 里出现）
        for api_name, methods in api_verbs.items():
            if api_name not in s:
                continue
            for meth, verb in methods.items():
                if verb != 'GET' and re.search(r'\\.%s\\s*\\(' % meth, s):
                    writes.add(('api:%s.%s' % (api_name, meth), verb))''')

io.open(P, 'w', encoding='utf-8').write(s)
print('  ✓ 已修正模板路径解析与 api 写操作识别')
