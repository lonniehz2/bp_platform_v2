# -*- coding: utf-8 -*-
"""接入「控制器文件名兜底」：仅当推导出的模块/资源为空时才兜底。"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))

SNIPPET = '''            if not module or not res:
                _fb = fallback_target(fn)
                if _fb:
                    res, module = _fb'''

for fn in ('_add_require_perm.py', '_gen_endpoint_perms.py'):
    p = os.path.join(HERE, fn)
    s = io.open(p, encoding='utf-8').read()
    if 'fallback_target(fn)' in s:
        print('%s 已接入' % fn)
        continue
    old = 'module = normalize_module(module, res)'
    if old not in s:
        print('%s 未找到 normalize 调用' % fn)
        continue
    s = s.replace(old, old + '\n' + SNIPPET, 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('%s：已接入兜底' % fn)

p = os.path.join(HERE, '_audit_perm_offline.py')
s = io.open(p, encoding='utf-8').read()
if 'fallback_target(fn)' not in s:
    old = '            module = RES_MODULE.get(res, module)'
    if old in s:
        s = s.replace(old, old + '''
        if not module or not res:
            _fb = fallback_target(fn)
            if _fb:
                res, module = _fb''', 1)
        io.open(p, 'w', encoding='utf-8', newline='').write(s)
        print('_audit_perm_offline.py：已接入兜底')
else:
    print('_audit_perm_offline.py 已接入')
