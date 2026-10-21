# -*- coding: utf-8 -*-
"""把表格里「直接输出原始编码」的写法改为走枚举标签。

问题：<el-tag>{{ row.depositStatus }}</el-tag> 会显示 REFUNDED、APPLYING 这类英文编码。
正确：{{ row.depositStatusLabel || enumLabel('depositStatus', row.depositStatus) }}

只处理名字以状态/类型/级别/结果等结尾的字段，避免误伤金额、姓名等。
"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
V = os.path.join(ROOT, 'frontend', 'src', 'views')

# 需要走枚举的字段后缀（含小写开头，如 source/channel）
SFX = ('Status', 'Type', 'Level', 'Result', 'Mode', 'Way', 'Category', 'Scope',
       'Source', 'Channel', 'Priority', 'Flag')

RAW = re.compile(r'\{\{\s*row\.([A-Za-z_]\w*)\s*\}\}')


def need_enum(field):
    return any(field.endswith(s) for s in SFX)


def main():
    changed = []
    for fn in sorted(os.listdir(V)):
        if not fn.endswith('.vue'):
            continue
        p = os.path.join(V, fn)
        s = io.open(p, encoding='utf-8').read()
        if 'row.' not in s:
            continue

        n = 0

        def repl(m):
            nonlocal n
            field = m.group(1)
            if not need_enum(field):
                return m.group(0)
            n += 1
            return "{{ row.%sLabel || enumLabel('%s', row.%s) }}" % (field, field, field)

        new = RAW.sub(repl, s)
        if n == 0:
            continue

        # 确保导入了 enumLabel
        if 'enumLabel' in new and "import { enumLabel }" not in new:
            m = re.search(r"^import .*from 'vue'\s*$", new, re.M)
            line = "import { enumLabel } from '@/constants/enums'"
            if m:
                new = new[:m.end()] + "\n" + line + new[m.end():]
            else:
                new = new.replace('<script setup>', "<script setup>\n" + line, 1)

        io.open(p, 'w', encoding='utf-8', newline='').write(new)
        changed.append((fn, n))

    total = sum(n for _, n in changed)
    for fn, n in changed:
        print('%-28s %d 处' % (fn, n))
    print('\n合计 %d 处，涉及 %d 个文件' % (total, len(changed)))


if __name__ == '__main__':
    main()
