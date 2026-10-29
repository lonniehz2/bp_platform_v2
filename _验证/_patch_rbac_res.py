# -*- coding: utf-8 -*-
import io

p = r'..\frontend\src\views\Rbac.vue'
s = io.open(p, encoding='utf-8').read()

# 资源字典补充
s = s.replace("  open: '开放平台', webhook: 'Webhook', screen2: '大屏'",
              "  open: '开放平台', webhook: 'Webhook', screen2: '大屏',\n"
              "  rules: '规则', credits: '信用', 'access-records': '通行记录',\n"
              "  idle: '空置分析', trace: '轨迹', 'untrusted-ratio': '异常比例',\n"
              "  verify: '核验', waitlist: '轮候', publicity: '公示', cohabitant: '同住人',\n"
              "  annualReview: '年审', inspectionPlan: '巡检计划', todo: '待办',\n"
              "  visits: '走访', dunning: '催缴', allotment: '配租', queue: '队列',\n"
              "  metrics: '指标', sys: '系统', config: '参数', audit: '审计',\n"
              "  command: '指令', report: '报表', billing: '计费', reconcile: '对账',\n"
              "  cashflow: '资金流水', grants: '授权', keyring: '钥匙', alerts: '告警',\n"
              "  complaints: '投诉', appeals: '申诉', visitsPlan: '走访计划',\n"
              "  staff: '员工', tenant: '承租人', platform: '平台', role: '角色', perm: '权限'",
              1)

# 资源未知时中文兜底
s = s.replace(".map(([rk, list]) => ({ key: rk, label: RES_LABEL[rk] || rk, items: list }))",
              ".map(([rk, list]) => ({ key: rk,\n"
              "  label: RES_LABEL[rk] || (/[\\u4e00-\\u9fa5]/.test(rk) ? rk : '其他'),\n"
              "  items: list }))", 1)

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('res labels updated')
