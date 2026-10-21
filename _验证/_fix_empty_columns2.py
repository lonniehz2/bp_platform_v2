# -*- coding: utf-8 -*-
"""补齐上一轮漏改的列模板（列名对了但模板仍引用旧字段）。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
V = os.path.join(ROOT, 'frontend', 'src', 'views')

FIXES = {
    'Subsidies.vue': [
        ("{{ row.subsidyModeLabel || enumLabel('subsidyMode', row.subsidyMode) }}",
         "{{ row.payModeLabel || enumLabel('payMode', row.payMode) }}"),
    ],
    'Keyring.vue': [
        ('{{ row.houseIdName || row.houseId }}',
         '{{ row.personIdName || row.personId }}'),
        ("enumLabel('keyringStatus', row.keyStatus)", "enumLabel('keyStatus', row.keyStatus)"),
    ],
    'Visits.vue': [
        ('prop="visitUserName" label="走访人" width="120" />',
         'prop="visitUserName" label="走访人" width="120">\n'
         '            <template #default="{ row }">{{ row.visitUserName || row.visitUserId || "-" }}</template>\n'
         '          </el-table-column>'),
    ],
}


def main():
    for fn, pairs in FIXES.items():
        p = os.path.join(V, fn)
        if not os.path.exists(p):
            print('跳过:', fn)
            continue
        s = io.open(p, encoding='utf-8').read()
        n = 0
        for a, b in pairs:
            if a in s:
                s = s.replace(a, b)
                n += 1
        io.open(p, 'w', encoding='utf-8', newline='').write(s)
        print('%-16s 修正 %d 处' % (fn, n))


if __name__ == '__main__':
    main()
