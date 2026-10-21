# -*- coding: utf-8 -*-
"""ID 字段全局排查：移除 Number() 转换。

风险：后端主键是 19 位雪花号，超过 Number.MAX_SAFE_INTEGER(2^53≈9e15)，
Number() 转换后多个 ID 会撞成同一个值（组织下拉「第N期小区」显示成第20期小区即此因）。

已确认安全（金额/计数/标志位，不需要改）：
  Number(d.total)、Number(row.isGranted)、Number(b.payableAmount)、Number(w.value)、
  Number(metrics.value.XXX)、Number(form.daysFromNow)
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
V = os.path.join(ROOT, 'frontend', 'src', 'views')

TARGETS = {
    'Persons.vue': [
        ('orgId: row.orgId ? Number(row.orgId) : null,', 'orgId: row.orgId ? String(row.orgId) : null,'),
        ('gf.personId = Number(row.id)', 'gf.personId = String(row.id)'),
        ('personId: Number(row.personId || row.id),', 'personId: String(row.personId || row.id),'),
        ('vf.personId = Number(row.id)', 'vf.personId = String(row.id)'),
    ],
    'Rbac.vue': [
        ('value: Number(r.id), label:', 'value: String(r.id), label:'),
        ('value: Number(p.id), label:', 'value: String(p.id), label:'),
    ],
}


def main():
    total = 0
    for fn, pairs in TARGETS.items():
        p = os.path.join(V, fn)
        if not os.path.exists(p):
            print('跳过（不存在）:', fn)
            continue
        s = io.open(p, encoding='utf-8').read()
        n = 0
        for a, b in pairs:
            if a in s:
                s = s.replace(a, b)
                n += 1
        io.open(p, 'w', encoding='utf-8', newline='').write(s)
        total += n
        print('%s：修正 %d 处' % (fn, n))

    # 复查：确认没有残留的 ID 类 Number 转换
    left = []
    for dirpath, _, files in os.walk(V):
        for fn in files:
            if not fn.endswith('.vue'):
                continue
            s = io.open(os.path.join(dirpath, fn), encoding='utf-8').read()
            for i, line in enumerate(s.splitlines(), 1):
                if 'Number(' not in line:
                    continue
                if any(k in line for k in ('total', 'isGranted', 'payableAmount', 'w.value',
                                           'metrics.value', 'daysFromNow', 'length', 'unread')):
                    continue
                if any(k in line for k in ('.id', 'Id')):
                    left.append('%s:%d: %s' % (fn, i, line.strip()))
    print('\n合计修正 %d 处' % total)
    print('残留可疑：%d 处' % len(left))
    for x in left[:10]:
        print('  ', x)


if __name__ == '__main__':
    main()
