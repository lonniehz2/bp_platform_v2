# -*- coding: utf-8 -*-
"""押金退款改为原子扣减（条件更新），避免并发超退。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'fin',
                 'service', 'impl', 'DepositRefundServiceImpl.java')
s = io.open(P, encoding='utf-8', errors='replace').read()

# 1) 校验段：改为原子条件扣减（不再只做读取校验）
OLD_CHECK = '''        // 押金退还：不得超过押金台账余额
        if ("DEPOSIT".equals(cmd.refundType()) && cmd.contractId() != null) {
            FinDeposit dep = depositMapper.selectOne(new LambdaQueryWrapper<FinDeposit>()
                    .eq(FinDeposit::getContractId, cmd.contractId()).last("LIMIT 1"));
            if (dep == null) {
                throw BizException.stateConflict("该合同无押金台账，无法退还押金");
            }
            if (amt.compareTo(money(dep.getBalanceAmount())) > 0) {
                throw BizException.paramInvalid(
                        "退款金额超过押金余额 " + money(dep.getBalanceAmount()));
            }
        }'''

NEW_CHECK = '''        // 押金退还：原子扣减（条件更新），并发下不会超退
        //   update ... set refund += amt, balance -= amt where contract_id=? and balance >= amt
        //   影响行数为 0 说明余额不足或台账不存在
        if ("DEPOSIT".equals(cmd.refundType()) && cmd.contractId() != null) {
            int affected = depositMapper.update(null,
                    new com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper
                            <FinDeposit>()
                            .eq(FinDeposit::getContractId, cmd.contractId())
                            .ge(FinDeposit::getBalanceAmount, amt)
                            .setSql("refund_amount = refund_amount + " + amt
                                    + ", balance_amount = balance_amount - " + amt));
            if (affected == 0) {
                FinDeposit dep = depositMapper.selectOne(new LambdaQueryWrapper<FinDeposit>()
                        .eq(FinDeposit::getContractId, cmd.contractId()).last("LIMIT 1"));
                if (dep == null) {
                    throw BizException.stateConflict("该合同无押金台账，无法退还押金");
                }
                throw BizException.paramInvalid(
                        "退款金额超过押金余额 " + money(dep.getBalanceAmount()));
            }
        }'''

if OLD_CHECK in s:
    s = s.replace(OLD_CHECK, NEW_CHECK, 1)
    print('退款校验已改为原子条件扣减')
else:
    print('未找到原校验段')

# 2) 删除原先事后的余额扣减块（已上移为原子操作，避免重复扣减）
OLD_DEDUCT = '''        // 押金退还：同步扣减押金台账余额
        if ("DEPOSIT".equals(e.getRefundType()) && e.getContractId() != null) {
            FinDeposit dep = depositMapper.selectOne(new LambdaQueryWrapper<FinDeposit>()
                    .eq(FinDeposit::getContractId, e.getContractId()).last("LIMIT 1"));
            if (dep != null) {
                dep.setRefundAmount(money(dep.getRefundAmount())
                        .add(money(e.getRefundAmount())).setScale(2, RoundingMode.HALF_UP));
                recalcDeposit(dep);
                dep.setUpdateTime(LocalDateTime.now());
                depositMapper.updateById(dep);
                log.info("押金退还：合同 {} 退还 {}，台账余额 {}", e.getContractId(),
                        e.getRefundAmount(), dep.getBalanceAmount());
            }
        }
'''
if OLD_DEDUCT in s:
    s = s.replace(OLD_DEDUCT, '', 1)
    print('已移除事后重复扣减')
else:
    print('未找到事后扣减段（可能已改）')

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('完成')
