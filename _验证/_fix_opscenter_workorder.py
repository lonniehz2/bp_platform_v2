# -*- coding: utf-8 -*-
"""运维操作台·工单流程：# 列名对齐 WorkOrderVO 真实字段

WorkOrderVO 字段是 workorderNo / orderType / orderStatus / orderTitle，
页面原先用的是 workOrderNo / workOrderType / title —— 全部取不到值，单元格空白。
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

PAIRS_UI = [
    ('prop="workOrderNo"', 'prop="workorderNo"'),
    ('prop="workOrderType"', 'prop="orderType"'),
    ("enumLabel('workOrderType', row.workOrderType)", "enumLabel('orderType', row.orderType)"),
    ('prop="workOrderStatus"', 'prop="orderStatus"'),
    ("enumLabel('workOrderStatus', row.workOrderStatus)", "enumLabel('orderStatus', row.orderStatus)"),
    ('prop="title" label=', 'prop="orderTitle" label='),
]


def main():
    p = os.path.join(ROOT, 'frontend', 'src', 'views', 'OpsCenter.vue')
    s = io.open(p, encoding='utf-8').read()
    n = 0
    for a, b in PAIRS_UI:
        if a in s:
            s = s.replace(a, b)
            n += 1
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('OpsCenter 列名修正 %d 组' % n)

    # 工单路由：/ops-center/:tab? 是路径参数，不能写成 ?tab=order
    p2 = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'msg',
                      'service', 'impl', 'TodoCenterServiceImpl.java')
    s2 = io.open(p2, encoding='utf-8').read()
    s2 = s2.replace('"/ops-center?tab=order&pending=1"', '"/ops-center/order?pending=1"')
    io.open(p2, 'w', encoding='utf-8', newline='').write(s2)
    print('工单路由改为路径参数:', '/ops-center/order?pending=1' in s2)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
