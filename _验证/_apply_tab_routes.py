# -*- coding: utf-8 -*-
"""给路由加可选 tab 参数：/rbac/:tab?、/sys/:tab?、/ops-center/:tab?

只改 path 一行，组件与 meta 不动；旧链接（无参数）依然可用。
"""
import io
import os

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'src')
ROUTER = os.path.join(BASE, 'router', 'index.js')

TARGETS = [
    ("path: '/rbac',", "path: '/rbac/:tab?',"),
    ("path: '/sys',", "path: '/sys/:tab?',"),
    ("path: '/ops-center',", "path: '/ops-center/:tab?',"),
]


def main():
    s = io.open(ROUTER, encoding='utf-8').read()
    for old, new in TARGETS:
        if new in s:
            print('已在：%s' % new)
            continue
        if old not in s:
            print('未找到：%s' % old)
            continue
        s = s.replace(old, new, 1)
        print('已改：%s -> %s' % (old.strip(), new.strip()))
    io.open(ROUTER, 'w', encoding='utf-8', newline='').write(s)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
