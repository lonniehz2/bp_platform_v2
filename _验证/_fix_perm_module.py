# -*- coding: utf-8 -*-
"""修正权限码推导：类级路径缺少模块段时（如 /api/v1/houses），按资源反查模块。

同时保证「生成权限码」与「补注解」两个脚本使用同一套推导规则。
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))

MODULE_SET = "'biz', 'fin', 'asset', 'person', 'iam', 'sys', 'msg', 'ops', 'rpt', 'open', 'gov'"

FALLBACK = '''
def normalize_module(module, resource):
    """把 housе/houses 这类资源反查成所属模块（asset/fin/...）。"""
    if module in (%s):
        return module
    return RES_MODULE.get(resource, module)
''' % MODULE_SET

for fn in ('_add_require_perm.py', '_gen_endpoint_perms.py'):
    p = os.path.join(HERE, fn)
    if not os.path.exists(p):
        print('%s 不存在' % fn)
        continue
    s = io.open(p, encoding='utf-8').read()
    if 'normalize_module' in s:
        print('%s 已有 normalize_module' % fn)
        continue
    # 插入函数（放在 RES_MODULE 之后）
    anchor = 'def segs(path):' if 'def segs(path):' in s else 'def module_of(path):'
    s = s.replace(anchor, FALLBACK.strip() + '\n\n\n' + anchor, 1)

    # 在推导权限码处应用修正
    if fn == '_add_require_perm.py':
        s = s.replace('''            module = module_of(base)
            res = resource_of(base)''',
                      '''            module = module_of(base)
            res = resource_of(base)
            module = normalize_module(module, res)''', 1)
    else:
        s = s.replace('''            if not module:
                module = ss[0]''',
                      '''            if not module:
                module = ss[0]
            module = normalize_module(module, res)''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('%s：已加模块反查' % fn)
