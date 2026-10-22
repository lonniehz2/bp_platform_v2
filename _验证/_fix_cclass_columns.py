# -*- coding: utf-8 -*-
"""C 类空列修正：换房/投诉/申诉/合同变更的字段映射。

依据接口实测字段：
  /exchanges  : oldHouseId + oldHouseIdName、newHouseId + newHouseIdName
  /complaints : submitterName、personIdName
  /appeals    : personIdName
  合同变更     : approveStatus（不是 changeStatus），changeNo 由后端派生
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
V = os.path.join(ROOT, 'frontend', 'src', 'views')

FIXES = {
    'Exchanges.vue': [
        ('prop="fromHouseId" label="原房源"', 'prop="oldHouseId" label="原房源"'),
        ('row.fromHouseIdName || row.fromHouseId', 'row.oldHouseIdName || row.oldHouseId'),
        ('prop="toHouseId" label="新源房"', 'prop="newHouseId" label="新入住"'),
        ('row.toHouseIdName || row.toHouseId', 'row.newHouseIdName || row.newHouseId'),
    ],
    'Complaints.vue': [
        ('row.complainantPersonIdName || row.complainantPersonId',
         'row.submitterName || row.personIdName || "-"'),
    ],
    'Appeals.vue': [
        ('row.applicantPersonIdName || row.applicantPersonId',
         'row.personIdName || row.personId'),
    ],
    'ContractChanges.vue': [
        ('prop="changeStatus"', 'prop="approveStatus"'),
        ('row.changeStatusLabel', 'row.approveStatusLabel'),
        ('row.changeStatus', 'row.approveStatus'),
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
        print('%-20s 修正 %d 处' % (fn, n))


if __name__ == '__main__':
    main()
