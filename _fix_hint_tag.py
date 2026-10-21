# -*- coding: utf-8 -*-
"""修复 HINT / TAG 未定义（生成器占位符残留），并完善检查脚本白名单"""
import io
import os
import re

V = r'D:\Work\业务平台开发\frontend\src\views'

# 每个页面的提示文案（与生成时的业务含义一致）
HINTS = {
    'Alerts': '阈值告警由规则引擎产生；可转工单、升级或忽略',
    'Appeals': '申诉期限默认 10 个自然日；逾期未处理会标记超时',
    'Cashflow': '核销/退款/补贴都会自动记账，形成完整资金流水',
    'Complaints': '投诉需在时限内办结，办结时填写处理意见',
    'ContractChanges': '调租/租期/承租人变更，批准后写回合同',
    'Credits': '失信限制再申请 5 年；到期可扫描自动失效',
    'Exchanges': '换房次数受限；「应换不换」按 1.5 倍租金计收',
    'GovReport': '报送任务按周期自动生成；失败可在任务详情重试',
    'HouseCalendar': '日房态用于短租与预订占用；改价只影响指定日期',
    'Keyring': '钥匙包绑定人员与通行介质；状态变更与回收需留痕',
    'OpenApps': '开放应用按 appKey 鉴权；密钥重置后旧密钥立即失效',
    'Publicities': '配租公示必须 ≥7 自然日且已结束才能签约',
    'ShortRent': '短租需实名登记；退房时刻必须晚于入住时刻',
    'Visits': '来访登记用于园区/小区出入管理，可关联被访人',
    'Waitlist': '总分 = 优先附加分 + 轮候天数 × 0.1；摇号按总分降序',
}

fixed_hint, fixed_tag = 0, 0
for f in os.listdir(V):
    if not f.endswith('.vue'):
        continue
    p = os.path.join(V, f)
    s = io.open(p, encoding='utf-8').read()
    orig = s

    if ':title="HINT"' in s:
        hint = HINTS.get(f[:-4], '操作前请确认业务前提条件')
        s = s.replace(':title="HINT"', ":title=\"'%s'\"" % hint.replace("'", "\\'"))
        fixed_hint += 1

    # v-if="TAG" 永远是 undefined → 该标签从不显示，直接去掉条件
    if 'v-if="TAG"' in s:
        s = s.replace('v-if="TAG" ', '')
        fixed_tag += 1

    if s != orig:
        io.open(p, 'w', encoding='utf-8').write(s)

print('  ✓ 修复 :title="HINT" %d 个页面' % fixed_hint)
print('  ✓ 修复 v-if="TAG" %d 个页面' % fixed_tag)

# ---------- 完善检查脚本 ----------
C = r'D:\Work\业务平台开发\_验证\_check_build.py'
c = io.open(C, encoding='utf-8').read()

# 白名单补充 Vue 内置
if "'$route'" not in c:
    c = c.replace("'w', 'y', 'z'\n}",
                  "'w', 'y', 'z',\n"
                  "    # Vue 模板内置\n"
                  "    '$route', '$router', '$emit', '$attrs', '$slots', '$props',\n"
                  "    '$refs', '$el', '$nextTick'\n}")
    io.open(C, 'w', encoding='utf-8').write(c)
    print('  ✓ 检查脚本白名单补 $route/$router 等')

# defineProps / defineEmits 视作声明
if 'defineProps' not in c:
    c = io.open(C, encoding='utf-8').read()
    c = c.replace("def defined_names(script):\n    names = set()",
                  "def defined_names(script):\n    names = set()\n"
                  "    # defineProps({ columns: ... }) 里的键也是可用标识符\n"
                  "    for m in re.finditer(r'defineProps(?:<[^>]*>)?\\s*\\(\\s*\\{([\\s\\S]{0,400}?)\\}', script):\n"
                  "        for k in re.findall(r'([A-Za-z_$][\\w$]*)\\s*:', m.group(1)):\n"
                  "            names.add(k)\n"
                  "    for m in re.finditer(r'defineProps\\(\\s*\\[([^\\]]*)\\]', script):\n"
                  "        for part in m.group(1).split(','):\n"
                  "            n = part.strip().strip(\"'\\\"\")\n"
                  "            if n:\n"
                  "                names.add(n)")
    io.open(C, 'w', encoding='utf-8').write(c)
    print('  ✓ 检查脚本识别 defineProps 声明的属性')
