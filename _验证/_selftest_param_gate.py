# -*- coding: utf-8 -*-
"""自检：临时注入一个后端不认识的参数，验证 --strict 关卡确实会失败，然后还原。

注意：注入点必须选「字面量参数对象」的调用。
透传式（{ params } / { ...obj }）在静态分析下看不到具体键，审计按设计跳过——
这也意味着该关卡有一条已知盲区，验证时不要选到这类调用。

用法：python _selftest_param_gate.py
"""
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DASH = os.path.abspath(os.path.join(HERE, '..', 'frontend', 'src', 'views', 'Dashboard.vue'))
PY = sys.executable

OLD = "{ params: { pageNum: 1, pageSize: 1 } })"
NEW = "{ params: { pageNum: 1, pageSize: 1, bogusParamXyz: 1 } })"


def main():
    src = io.open(DASH, encoding='utf-8').read()
    if OLD not in src:
        print('锚点未找到，跳过自检')
        return 2
    try:
        io.open(DASH, 'w', encoding='utf-8', newline='').write(src.replace(OLD, NEW, 1))
        p = subprocess.run([PY, os.path.join(HERE, '_audit_params.py'), '--strict'],
                           cwd=HERE, capture_output=True, text=True, encoding='utf-8',
                           errors='replace')
        hit = 'bogusParamXyz' in (p.stdout or '')
        print('注入后审计退出码:', p.returncode, '| 是否报出注入参数:', hit)
        ok = (p.returncode == 1) and hit
        print('关卡自检:', '✔ 能拦住' if ok else '✘ 拦不住（关卡无效）')
        return 0 if ok else 1
    finally:
        io.open(DASH, 'w', encoding='utf-8', newline='').write(src)
        print('已还原 Dashboard.vue')


if __name__ == '__main__':
    raise SystemExit(main())
