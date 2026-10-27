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
    narrow = []
    for dirpath, _, files in os.walk(SRC):
        if 'node_modules' in dirpath:
            continue
        for fn in files:
            if not fn.endswith(('.vue', '.js')):
                continue
            path = os.path.join(dirpath, fn)
            text = io.open(path, encoding='utf-8', errors='replace').read()
            lines = text.splitlines()
            for lineno, line in enumerate(lines, 1):
                stripped = line.strip()
                if 'Number(' in line and not (stripped.startswith('//') or stripped.startswith('*')):
                    for m in re.finditer(r'Number\(([^()]*)\)', line):
                        arg = m.group(1).strip()
                        if not ID_LIKE.search(arg):
                            continue
                        if SAFE.match('Number(' + arg + ')'):
                            continue
                        bad.append((os.path.relpath(path, SRC), lineno, stripped))
                        break
                # ID 输入框过窄：19 位雪花号需要约 200px，否则后几位被藏掉
                if re.search(r'v-model="[^"]*[Ii]d"', line):
                    # 只取当前标签块，避免把下一行相邻控件的宽度算进来
                    block = line
                    j = lineno
                    while j < len(lines) and '/>' not in block and '>' not in block:
                        block += ' ' + lines[j].strip()
                        j += 1
                    w = re.search(r'width[:=]"?\s*(\d+)px', block)
                    if w and int(w.group(1)) < 200:
                        narrow.append((os.path.relpath(path, SRC), lineno, stripped))
    return bad, narrow


def main():
    bad, narrow = scan()
    print('扫描目录：frontend/src')
    ok = True
    if bad:
        ok = False
        print('✘ %d 处对 ID 使用了 Number()（19 位雪花号超出 Number 精度，请用 String）\n' % len(bad))
        for f, ln, code in bad:
            print('  %s:%d  %s' % (f, ln, code[:110]))
    else:
        print('✔ ID 精度：未发现 Number() 转换 ID')

    if narrow:
        ok = False
        print('\n✘ %d 处 ID 输入框宽度 < 200px（19 位 ID 显示不全，用户会误以为位数受限）\n'
              % len(narrow))
        for f, ln, code in narrow:
            print('  %s:%d  %s' % (f, ln, code[:110]))
    else:
        print('✔ ID 输入框：宽度均 ≥ 200px')

    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
