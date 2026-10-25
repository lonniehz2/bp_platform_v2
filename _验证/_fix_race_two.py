# -*- coding: utf-8 -*-
"""两处资金/状态并发加固：抄表出账、催缴动作执行改为条件更新。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
FIN = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'fin')

# ---------- 1) 抄表出账：条件更新 bill_id ----------
P = os.path.join(FIN, 'service', 'impl', 'MeterReadingServiceImpl.java')
s = io.open(P, encoding='utf-8', errors='replace').read()
if 'race:ignore' not in s and 'setSql("bill_id' not in s:
    # 在创建账单后、回写读数前，改为条件更新（bill_id is null 才能占位）
    idx = s.find('public BillVO bill(')
    seg = s[idx:idx + 6000] if idx > 0 else ''
    if 'e.setBillId(' in seg and 'mapper.updateById(e)' in seg:
        print('抄表出账：存在回写逻辑，改为条件更新')
        seg2 = seg.replace('''            e.setBillId(billId);''',
'''            // 并发保护：仅当 bill_id 为空时占位，避免同一读数重复出账
            int claimed = mapper.update(null,
                    new com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper
                            <com.yundao.bp.fin.entity.FinMeterReading>()
                            .eq(com.yundao.bp.fin.entity.FinMeterReading::getId, id)
                            .isNull(com.yundao.bp.fin.entity.FinMeterReading::getBillId)
                            .set(com.yundao.bp.fin.entity.FinMeterReading::getBillId, billId));
            if (claimed == 0) {
                throw BizException.stateConflict("该抄表记录已出账");
            }
            e.setBillId(billId);''', 1)
        s = s[:idx] + seg2 + s[idx + 6000:]
        io.open(P, 'w', encoding='utf-8', newline='').write(s)
    else:
        print('抄表出账：未找到回写语句，跳过')

# ---------- 2) 催缴动作执行：条件更新状态 ----------
Q = os.path.join(FIN, 'service', 'impl', 'ArrearsActionServiceImpl.java')
t = io.open(Q, encoding='utf-8', errors='replace').read()
if 'race:ignore' not in t and 'setSql("action_status' not in t:
    old = '''        if (from == ArrearsActionStatus.EXECUTED) {
            throw BizException.stateConflict("处置单已执行");
        }'''
    new = '''        // 并发保护：用条件更新抢占执行权，避免同一处置单被并发执行两次
        int claimed = mapper.update(null,
                new com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper
                        <com.yundao.bp.fin.entity.FinArrearsAction>()
                        .eq(com.yundao.bp.fin.entity.FinArrearsAction::getId, id)
                        .ne(com.yundao.bp.fin.entity.FinArrearsAction::getActionStatus,
                                ArrearsActionStatus.EXECUTED.name())
                        .set(com.yundao.bp.fin.entity.FinArrearsAction::getActionStatus,
                                ArrearsActionStatus.EXECUTED.name()));
        if (claimed == 0) {
            throw BizException.stateConflict("处置单已执行");
        }
        if (from == ArrearsActionStatus.EXECUTED) {
            throw BizException.stateConflict("处置单已执行");
        }'''
    if old in t:
        t = t.replace(old, new, 1)
        io.open(Q, 'w', encoding='utf-8', newline='').write(t)
        print('催缴执行：已改为条件更新')
    else:
        print('催缴执行：未找到状态校验，跳过')
print('完成')
