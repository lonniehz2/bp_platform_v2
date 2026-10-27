# -*- coding: utf-8 -*-
"""仪表盘指标卡口径提示。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
p = os.path.join(ROOT, 'frontend', 'src', 'views', 'Dashboard.vue')
s = io.open(p, encoding='utf-8').read()

TIPS = {
    '房源结构': '按房源状态拆分：已出租 / 空置可租 / 待配租 / 其他，总数=房源台账条数',
    '房源概况': '已出租=状态 OCCUPIED；空置可租=VACANT；出租率=已出租÷房源总数',
    '财务应收': '欠费金额=应收−已缴的正数部分；收缴率=累计收款÷累计应收',
    '申请与审批': '待受理=已提交未受理；审核中=受理后未终审；已通过=终审通过',
    '押金与退款': '押金按收取/退还/待退三态统计，金额单位元',
    '服务与待办': '工单与告警按待处理/处理中/已处理统计，含今日新增',
}

for title, tip in TIPS.items():
    needle = '<span class="t">%s</span>' % title
    if needle in s:
        s = s.replace(
            needle,
            '<el-tooltip content="%s" placement="top">'
            '<span class="t" style="cursor:help">%s <span class="muted">ⓘ</span></span>'
            '</el-tooltip>' % (tip, title), 1)
        print('已加提示:', title)

io.open(p, 'w', encoding='utf-8', newline='').write(s)
