# -*- coding: utf-8 -*-
"""修掉 7 个页面的空列：列名与后端返回字段不符。

依据各接口真实返回字段（实测）：
  /fin/subsidies/records : payMode, payModeLabel, personIdName, recordStatus ...
  /complaints            : handleStatus, submitterName, personIdName, complaintType ...
  /appeals               : personIdName, appealStatus, appealType ...
  /credits               : violationType, sanctionType, status, banEndDate, personIdName ...
  /visits                : visitUserName, personIdName, visitStatus ...
  /keyring               : keyAlias, keyStatus, keyType, personIdName（无 houseId/keyCount）
  /allocation/waiting    : liveWaitDays, personIdName, priorityScore ...
"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
V = os.path.join(ROOT, 'frontend', 'src', 'views')

# (文件, [(旧, 新), ...])
FIXES = {
    'Subsidies.vue': [
        ('prop="subsidyMode" label="方式"', 'prop="payMode" label="发放方式"'),
        ('{{ row.payMode }}', "{{ row.payModeLabel || enumLabel('payMode', row.payMode) }}"),
        ('{{ row.personId }}', '{{ row.personIdName || row.personName || row.personId }}'),
    ],
    'Complaints.vue': [
        ('prop="complaintStatus"', 'prop="handleStatus"'),
        ('row.complaintStatus', 'row.handleStatus'),
        ('prop="complainantPersonId" label="投诉人"', 'prop="submitterName" label="投诉人"'),
        ("{{ row.complainantPersonId }}", '{{ row.submitterName || row.personIdName || "-" }}'),
    ],
    'Appeals.vue': [
        ('prop="applicantPersonId" label="申请人"', 'prop="personIdName" label="申请人"'),
        ("{{ row.applicantPersonId }}", '{{ row.personIdName || row.personId }}'),
    ],
    'Credits.vue': [
        ('prop="creditType"', 'prop="violationType"'),
        ('row.creditType', 'row.violationType'),
        ("enumLabel('creditType', row.creditType)", "enumLabel('violationType', row.violationType)"),
        ('prop="creditLevel"', 'prop="sanctionType"'),
        ('row.creditLevel', 'row.sanctionType'),
        ("enumLabel('creditLevel', row.creditLevel)", "enumLabel('sanctionType', row.sanctionType)"),
        ('prop="creditStatus"', 'prop="status"'),
        ('row.creditStatus', 'row.status'),
        ("enumLabel('creditStatus', row.creditStatus)", "enumLabel('status', row.status)"),
        ('prop="endDate" label="截止"', 'prop="banEndDate" label="惩戒截止"'),
        ('{{ row.personId }}', '{{ row.personIdName || row.personId }}'),
    ],
    'Visits.vue': [
        ('prop="visitorName" label="来访人"', 'prop="visitUserName" label="走访人"'),
        ("{{ row.visitorName }}", '{{ row.visitUserName || "-" }}'),
        ('prop="personId" label="被访人"', 'prop="personIdName" label="被访人"'),
    ],
    'Waitlist.vue': [
        ('prop="waitDays" label="轮候天数"', 'prop="liveWaitDays" label="已轮候天数"'),
        ('prop="personId" label="人员"', 'prop="personIdName" label="轮候人"'),
        ('{{ row.personName || row.personId }}', '{{ row.personIdName || row.personId }}'),
    ],
    'Keyring.vue': [
        ('prop="keyringNo" label="编号"', 'prop="keyAlias" label="钥匙别名"'),
        ('prop="houseId" label="房源"', 'prop="personIdName" label="持有人"'),
        ('prop="keyringStatus"', 'prop="keyStatus"'),
        ('row.keyringStatus', 'row.keyStatus'),
    ],
}


def main():
    total = 0
    for fn, pairs in FIXES.items():
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
        # 钥匙包：删除后端不存在的「钥匙数」列（整列会在界面上空白）
        if fn == 'Keyring.vue':
            s2 = re.sub(r'\s*<el-table-column prop="keyCount"[^>]*/>', '', s)
            s2 = re.sub(r'\s*<el-table-column prop="keyCount"[\s\S]*?</el-table-column>', '', s2)
            if s2 != s:
                s = s2
                n += 1
        # 补齐 enumLabel 导入
        if 'enumLabel' in s and "import { enumLabel }" not in s:
            m = re.search(r"^import .*from 'vue'\s*$", s, re.M)
            if m:
                s = s[:m.end()] + "\nimport { enumLabel } from '@/constants/enums'" + s[m.end():]
                n += 1
        io.open(p, 'w', encoding='utf-8', newline='').write(s)
        total += n
        print('%-16s 修正 %d 处' % (fn, n))
    print('合计 %d 处' % total)


if __name__ == '__main__':
    main()
