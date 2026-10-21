# -*- coding: utf-8 -*-
"""把 _audit_params.py 的前端扫描改为「按调用粒度」判定。

原实现：某路径只要出现一次透传调用（{ params }），整条路径的未接参数与拼写检查都被跳过。
问题：同一接口常既有透传也有字面量调用，一处透传会掩盖其他调用的错误参数。

改为：keys 只收集字面量键；透传调用只跳过自身，不影响同路径其它调用。
"""
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, '_audit_params.py')

NEW_FN = '''def scan_frontend():
    """返回 {path: {'keys': set, 'literal': bool}}

    keys 只收集「字面量参数对象」里的键；literal 表示该路径存在可静态分析的调用。
    透传式（{ params } / { params: obj }）无法得知具体键，只跳过该次调用本身，
    不能因此把整条路径的检查都跳过——同一接口往往既有透传也有字面量调用。
    """
    out = {}
    for dirpath, _, files in os.walk(FE):
        if 'node_modules' in dirpath:
            continue
        for fn in files:
            if not fn.endswith(('.js', '.vue')):
                continue
            src = io.open(os.path.join(dirpath, fn), encoding='utf-8', errors='replace').read()
            for m in re.finditer(r"req\\.get\\(\\s*['\\"`]([^'\\"`]+)['\\"`]\\s*,\\s*\\{", src):
                path = norm_path(m.group(1))
                slot = out.setdefault(path, {'keys': set(), 'literal': False})
                tail = src[m.end(): m.end() + 600]
                if re.match(r'\\s*params\\s*[,}]', tail) or \\
                   re.match(r'\\s*params\\s*:\\s*[A-Za-z_$][\\w$]*\\s*[,}]', tail):
                    continue
                pm = re.search(r'params:\\s*\\{([^}]*)\\}', tail)
                if not pm:
                    continue
                for part in pm.group(1).split(','):
                    k = part.split(':')[0].strip()
                    if re.fullmatch(r'[A-Za-z_$][\\w$]*', k):
                        slot['keys'].add(k)
                        slot['literal'] = True
    return out
'''


def main():
    s = io.open(P, encoding='utf-8').read()
    i = s.find('def scan_frontend():')
    j = s.find('\ndef main(', i)
    if i < 0 or j < 0:
        print('未找到 scan_frontend 或 main，跳过')
        return 2
    s = s[:i] + NEW_FN + s[j:]
    # 调用侧适配新结构
    s = s.replace("        used = fe.get(api_path, set())\n        if '*' in used:\n            continue          # 透传式调用：页面自行决定参数，不算缺失\n",
                  "        slot = fe.get(api_path) or {}\n        used = slot.get('keys', set())\n")
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('scan_frontend 已改为按调用粒度；调用侧已适配')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
