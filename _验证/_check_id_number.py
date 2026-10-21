# -*- coding: utf-8 -*-
"""静态检查：禁止对 ID 字段使用 Number() 转换。

背景：后端主键是 19 位雪花号（约 1e18），超过 JS 的 Number 安全整数上限 2^53。
一旦 Number() 转换，末几位会被抹掉，多个 ID 撞成同一个值——
已因此出现过「组织下拉选第N期小区却总显示第20期小区」。

后端把 Long 统一序列化为字符串，前端只要不擅自转数字就是安全的。
本脚本在回归里守住这条线。

用法：python _check_id_number.py  （有违规则退出码 1）
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(os.path.join(HERE, '..', 'frontend', 'src'))

# 允许的 Pattern：金额、计数、标志位、指标、天数、长度等非 ID 字段
SAFE = re.compile(
    r'Number\(\s*('
    r'd\.total|total|rows\.length|length|unread'
    r'|row\.isGranted|isGranted'
    r'|[\w.]*(amount|Amount|price|Price|rent|Rent|deposit|Deposit|score|Score)'
    r'|metrics\.value[\w.]*'
    r'|[\w.]*(daysFromNow|days|Days|rate|Rate|percent|Percent)'
    r'|[\w.]*(count|Count|num|Num|value|Value)\b'
    r')'
)

# 视为 ID 的写法：xxx.id / xxx.Id / xxx_id / personId / orgId ...
ID_LIKE = re.compile(r'[A-Za-z_][\w.]*(?:\.id|\.Id|[a-z]Id|[a-z]_id)\b')


def scan():
    bad = []
    for dirpath, _, files in os.walk(SRC):
        if 'node_modules' in dirpath:
            continue
        for fn in files:
            if not fn.endswith(('.vue', '.js')):
                continue
            path = os.path.join(dirpath, fn)
            text = io.open(path, encoding='utf-8', errors='replace').read()
            for lineno, line in enumerate(text.splitlines(), 1):
                if 'Number(' not in line:
                    continue
                stripped = line.strip()
                if stripped.startswith('//') or stripped.startswith('*'):
                    continue
                for m in re.finditer(r'Number\(([^()]*)\)', line):
                    arg = m.group(1).strip()
                    if not ID_LIKE.search(arg):
                        continue
                    if SAFE.match('Number(' + arg + ')'):
                        continue
                    bad.append((os.path.relpath(path, SRC), lineno, stripped))
                    break
    return bad


def main():
    bad = scan()
    print('扫描目录：frontend/src')
    if not bad:
        print('✔ 未发现对 ID 字段使用 Number() 的写法')
        return 0
    print('✘ 发现 %d 处：ID 请用 String() 或原样传递（19 位雪花号超出 Number 精度）\n' % len(bad))
    for f, ln, code in bad:
        print('  %s:%d  %s' % (f, ln, code[:110]))
    return 1


if __name__ == '__main__':
    sys.exit(main())
