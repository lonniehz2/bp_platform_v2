# -*- coding: utf-8 -*-
"""补齐剩余枚举 + ID 名称，重建前后端"""
import io
import os
import re

FE = r'D:\Work\业务平台开发\frontend\src\constants\enums.js'

# ---------- 1) enums.js 补 15 个 ----------
NEW = {
    'AUTO': '自动出账', 'CONTRACT': '合同', 'HOUSE': '实物配租',
    'LOCK': '门锁', 'NONE': '无', 'OFFSET': '抵扣租金', 'ON_TIME': '按时完成',
    'PAPER': '纸质签署', 'RECONCILED': '已对账', 'SAFETY': '安全隐患',
    'SUBMIT': '提交', 'TENANT_APP': '租客端', 'VERIFIED': '已核验',
    'WIFI_LOCK': '无线门锁', 'TEST': '测试数据',
}
s = io.open(FE, encoding='utf-8').read()
add = [(k, v) for k, v in NEW.items()
       if re.search(r"^\s*'?%s'?\s*:" % k, s, re.M) is None]
if add:
    block = '\n  // ---------- 补充（审计发现） ----------\n'
    for k, v in add:
        block += "  %s: '%s',\n" % (k, v)
    s = s.replace('  // ---------- 房源 / 空间 ----------',
                  block + '\n  // ---------- 房源 / 空间 ----------', 1)
    io.open(FE, 'w', encoding='utf-8').write(s)
    print('  ✓ enums.js 补 %d 个：%s' % (len(add), ', '.join(k for k, _ in add)))

# ---------- 2) 重新生成 EnumLabels ----------
es = io.open(FE, encoding='utf-8').read()
m = re.search(r'const GLOBAL = \{(.*?)\n\}', es, re.S)
pairs = re.findall(r"^\s*'?([A-Z][A-Z_0-9]*)'?:\s*'([^']+)'", m.group(1), re.M)
seen, order = {}, []
for k, v in pairs:
    if k not in seen:
        seen[k] = v
        order.append(k)

OUT = (r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
       r'\common\util\EnumLabels.java')
tmpl = io.open(OUT, encoding='utf-8').read()
body = ',\n'.join('            new String[]{"%s", "%s"}' % (k, seen[k]) for k in order)
tmpl = re.sub(r'(List\.of\(\n)([\s\S]*?)(\n        \);)',
              lambda mm: mm.group(1) + body + mm.group(3), tmpl, count=1)
io.open(OUT, 'w', encoding='utf-8').write(tmpl)
print('  ✓ EnumLabels.java 更新为 %d 条' % len(seen))

# ---------- 3) Enricher 补 ID 解析 ----------
P = (r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
     r'\common\web\DisplayEnricher.java')
e = io.open(P, encoding='utf-8').read()
if 'feeItemId' not in e:
    e = e.replace('''            case "userId", "decideUserId", "handleUserId", "operatorId",
                 "assignUserId" -> bizNo("bp_iam_user", "username", "userId", id);''',
                  '''            case "userId", "decideUserId", "handleUserId", "operatorId",
                 "assignUserId", "approveById" -> bizNo("bp_iam_user", "username", "userId", id);
            case "feeItemId" -> bizNo("bp_fin_fee_item", "item_name", "feeItemId", id);
            case "standardId" -> bizNo("bp_fin_subsidy_standard", "standard_name", "standardId", id);
            case "ownerOrgId" -> bizNo("bp_iam_org", "org_name", "ownerOrgId", id);
            case "deviceId" -> bizNo("bp_dev_device", "device_code", "deviceId", id);''', 1)
    io.open(P, 'w', encoding='utf-8').write(e)
    print('  ✓ Enricher 补 feeItem/standard/ownerOrg/device 解析')
