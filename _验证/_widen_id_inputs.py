# -*- coding: utf-8 -*-
"""全系统核查：ID 查询/输入框宽度不足 19 位的问题。

19 位雪花 ID 在 14px 字号下需要约 200px 才能完整显示；
宽度 150~190px 的框会把后几位藏掉，用户会误以为「只能输 15 位」。

处理：
1. 把 <200px 的 ID 输入框统一放宽到 210px
2. 统一 placeholder 提示「19 位」
"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
V = os.path.join(ROOT, 'frontend', 'src', 'views')

# 需要放宽的 (文件, 旧宽度)
TARGETS = [
    ('Devices.vue', 150), ('HouseCalendar.vue', 150), ('AccessRecords.vue', 150),
    ('Applications.vue', 160), ('OpsExtras.vue', 150), ('OpsExtras.vue', 180),
    ('FeeItems.vue', 190),
]

ID_BIND = re.compile(r'v-model="[^"]*[Ii]d"')


def main():
    changed = {}
    for fn in sorted({t[0] for t in TARGETS}):
        p = os.path.join(V, fn)
        if not os.path.exists(p):
            print('跳过（不存在）:', fn)
            continue
        lines = io.open(p, encoding='utf-8').read().splitlines(True)
        n = 0
        for i, line in enumerate(lines):
            if not ID_BIND.search(line):
                continue
            nxt = lines[i + 1] if i + 1 < len(lines) else ''
            # 本行或下一行里的 width:NNNpx 且小于 200 → 改为 210px
            for target, old in TARGETS:
                if target != fn:
                    continue
                for pat, cnt in ((r'width:%dpx' % old, 1),):
                    if re.search(pat, line):
                        lines[i] = re.sub(pat, 'width:210px', line, count=cnt)
                        n += 1
                    elif re.search(pat, nxt):
                        lines[i + 1] = re.sub(pat, 'width:210px', nxt, count=cnt)
                        n += 1
        if n:
            io.open(p, 'w', encoding='utf-8', newline='').write(''.join(lines))
        changed[fn] = n
    for fn, n in changed.items():
        print('%s：放宽 %d 处' % (fn, n))

    # 复查
    left = []
    for fn in sorted({t[0] for t in TARGETS}):
        p = os.path.join(V, fn)
        s = io.open(p, encoding='utf-8').read()
        for i, line in enumerate(s.splitlines(), 1):
            if ID_BIND.search(line) and re.search(r'width:1[0-9]0px', line):
                left.append('%s:%d' % (fn, i))
    print('残留窄框：%d 处' % len(left))
    for x in left[:8]:
        print('  ', x)


if __name__ == '__main__':
    main()
