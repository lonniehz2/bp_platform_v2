# -*- coding: utf-8 -*-
"""修正 exchangeLimitReached 语义：表示"该租期已无换房次数"而非"本次是第几次" """
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'

# ---------- 1. VO：字段语义明确 + 由已完成次数决定 ----------
p1 = os.path.join(BASE, r'biz\dto\ExchangeVO.java')
s1 = io.open(p1, encoding='utf-8').read()

s1 = s1.replace('''        Boolean forced,
        /** 是否已超成都"限换 1 次" */
        Boolean exchangeLimitReached,''',
                '''        Boolean forced,
        /**
         * 是否已无换房次数（成都限 1 次）。
         *
         * <p>语义：<b>该租期已完成换房次数 ≥ 上限</b>，即"不能再换"，
         * 而非"本次是第几次"。首次申请（未完成过换房）应为 false。
         */
        Boolean exchangeLimitReached,''')

s1 = s1.replace('''        int times = e.getExchangeTimes() == null ? 0 : e.getExchangeTimes();''',
                '''        int times = e.getExchangeTimes() == null ? 0 : e.getExchangeTimes();
        // 仅"已完成"的换房才消耗次数；已无次数 = 已完成次数 >= 1（成都限 1 次）
        boolean noQuota = ExchangeStatus.COMPLETED.name().equals(e.getExchangeStatus());''')

s1 = s1.replace('                times, e.getIsForced() != null && e.getIsForced() == 1,\n                times >= 1,',
                '                times, e.getIsForced() != null && e.getIsForced() == 1,\n                noQuota,')

io.open(p1, 'w', encoding='utf-8').write(s1)
print('  ✓ ExchangeVO.exchangeLimitReached 语义已修正')

# ---------- 2. 服务：申请时返回"剩余次数"更直观 ----------
p2 = os.path.join(BASE, r'biz\service\impl\ExchangeServiceImpl.java')
s2 = io.open(p2, encoding='utf-8').read()
if 'remainingQuota' not in s2:
    s2 = s2.replace('''        log.info("换房申请 {}：合同 {} 房源 {} → {}（{}，第 {} 次）",''',
                    '''        log.info("换房申请 {}：合同 {} 房源 {} → {}（{}，本租期第 {} 次，剩余次数 {}）",''')
    s2 = s2.replace('''                type.label(), e.getExchangeTimes());''',
                    '''                type.label(), e.getExchangeTimes(),
                Math.max(0, MAX_EXCHANGE_TIMES - done - 1));''')
    io.open(p2, 'w', encoding='utf-8').write(s2)
    print('  ✓ 申请日志增加剩余次数')
