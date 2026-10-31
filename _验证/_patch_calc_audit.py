# -*- coding: utf-8 -*-
import io

# ---------- 1) 退租结算：押金取台账余额、欠费按合同且含减免/滞纳金 ----------
p = r'..\backend\src\main\java\com\yundao\bp\biz\service\impl\TerminationServiceImpl.java'
s = io.open(p, encoding='utf-8').read()
old = '''                java.util.List<java.math.BigDecimal> d = jdbc.queryForList(
                        "select deposit_amount from bp_biz_contract where id = ?",
                        java.math.BigDecimal.class, e.getContractId());
                if (!d.isEmpty() && d.get(0) != null) {
                    deposit = d.get(0);
                }
                java.util.List<java.math.BigDecimal> a = jdbc.queryForList(
                        "select coalesce(sum(bill_amount - paid_amount - waived_amount),0) "
                                + "from bp_fin_bill where house_id = ? and status in "
                                + "('UNPAID','PARTIAL','OVERDUE') and is_deleted = 0",
                        java.math.BigDecimal.class, e.getHouseId());
                if (!a.isEmpty() && a.get(0) != null) {
                    arrears = a.get(0);
                }'''
new = '''                // 押金以台账实际余额为准（已抵扣/已退部分不能再退），无台账才回退合同金额
                java.util.List<java.math.BigDecimal> d = jdbc.queryForList(
                        "select balance_amount from bp_fin_deposit "
                                + "where contract_id = ? and is_deleted = 0 order by id desc limit 1",
                        java.math.BigDecimal.class, e.getContractId());
                if (!d.isEmpty() && d.get(0) != null) {
                    deposit = d.get(0);
                } else {
                    java.util.List<java.math.BigDecimal> c = jdbc.queryForList(
                            "select deposit_amount from bp_biz_contract where id = ?",
                            java.math.BigDecimal.class, e.getContractId());
                    if (!c.isEmpty() && c.get(0) != null) {
                        deposit = c.get(0);
                    }
                }
                // 欠费只算本合同的未结账单：应收 - 减免 + 滞纳金 - 已收 - 已免
                java.util.List<java.math.BigDecimal> a = jdbc.queryForList(
                        "select coalesce(sum(bill_amount - discount_amount + late_fee "
                                + "- paid_amount - waived_amount),0) "
                                + "from bp_fin_bill where contract_id = ? and bill_status in "
                                + "('UNPAID','PARTIAL','OVERDUE') and is_deleted = 0",
                        java.math.BigDecimal.class, e.getContractId());
                if (!a.isEmpty() && a.get(0) != null) {
                    arrears = a.get(0);
                }'''
if old not in s:
    raise SystemExit('termination query block not found')
s = s.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('termination settlement fixed')

# ---------- 2) 押金退款：创建后刷新状态；驳回时回补余额 ----------
p = r'..\backend\src\main\java\com\yundao\bp\fin\service\impl\DepositRefundServiceImpl.java'
s = io.open(p, encoding='utf-8').read()
anchor = '''        refundMapper.insert(e);
        return RefundVO.from(e);
    }'''
new_anchor = '''        refundMapper.insert(e);

        // 原子扣减后同步押金状态（避免余额为 0 但状态仍是已收取）
        if ("DEPOSIT".equals(cmd.refundType()) && cmd.contractId() != null) {
            FinDeposit dep = depositMapper.selectOne(new LambdaQueryWrapper<FinDeposit>()
                    .eq(FinDeposit::getContractId, cmd.contractId()).last("LIMIT 1"));
            if (dep != null) {
                recalcDeposit(dep);
                dep.setUpdateTime(LocalDateTime.now());
                depositMapper.updateById(dep);
            }
        }
        return RefundVO.from(e);
    }'''
if anchor in s:
    s = s.replace(anchor, new_anchor, 1)

old_reject = '''        e.setRefundReason(reason);
        e.setUpdateTime(LocalDateTime.now());
        refundMapper.updateById(e);
        return RefundVO.from(e);'''
new_reject = '''        e.setRefundReason(reason);
        e.setUpdateTime(LocalDateTime.now());
        refundMapper.updateById(e);

        // 退款创建时已扣减押金余额；驳回需原路回补，避免钱被“吞掉”
        if ("DEPOSIT".equals(e.getRefundType()) && e.getContractId() != null) {
            BigDecimal amt = money(e.getRefundAmount());
            int restored = depositMapper.update(null,
                    new com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper
                            <FinDeposit>()
                            .eq(FinDeposit::getContractId, e.getContractId())
                            .ge(FinDeposit::getRefundAmount, amt)
                            .setSql("refund_amount = refund_amount - " + amt
                                    + ", balance_amount = balance_amount + " + amt));
            FinDeposit dep = depositMapper.selectOne(new LambdaQueryWrapper<FinDeposit>()
                    .eq(FinDeposit::getContractId, e.getContractId()).last("LIMIT 1"));
            if (dep != null) {
                recalcDeposit(dep);
                dep.setUpdateTime(LocalDateTime.now());
                depositMapper.updateById(dep);
            }
            log.info("退款 {} 驳回，回补押金 {}（影响 {} 行）", e.getRefundNo(), amt, restored);
        }
        return RefundVO.from(e);'''
if old_reject in s:
    s = s.replace(old_reject, new_reject, 2)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('deposit refund restored')

# ---------- 3) 补贴标准生效期按补贴周期判断 ----------
p = r'..\backend\src\main\java\com\yundao\bp\fin\service\impl\SubsidyServiceImpl.java'
s = io.open(p, encoding='utf-8').read()
s = s.replace('return calc(std, ct, cmd.area(), cmd.personCount(), cmd.monthlyRent());',
              'return calc(std, ct, cmd.area(), cmd.personCount(), cmd.monthlyRent(), cmd.subsidyPeriod());', 1)
s = s.replace('SubsidyCalcResult r = calc(std, ct, null, null, null);',
              'SubsidyCalcResult r = calc(std, ct, null, null, null, subsidyPeriod);', 2)
s = s.replace('private SubsidyCalcResult calc(FinSubsidyStandard std, BizContract ct, BigDecimal areaIn,\n'
              '                                   Integer personIn, BigDecimal rentIn) {',
              'private SubsidyCalcResult calc(FinSubsidyStandard std, BizContract ct, BigDecimal areaIn,\n'
              '                                   Integer personIn, BigDecimal rentIn, String period) {', 1)
s = s.replace('FinSubsidyStandard resolveStandard(Long standardId, BizContract ct) {',
              'FinSubsidyStandard resolveStandard(Long standardId, BizContract ct, String period) {', 1)
s = s.replace('String securityType = mapSecurityType(ct.getContractType());\n        LocalDate today = LocalDate.now();',
              'String securityType = mapSecurityType(ct.getContractType());\n'
              '        LocalDate today = LocalDate.now();\n'
              '        if (period != null && period.matches("\\\\d{4}-\\\\d{2}")) {\n'
              '            today = java.time.YearMonth.parse(period).atEndOfMonth();\n'
              '        }', 1)
s = s.replace('FinSubsidyStandard std = resolveStandard(cmd.standardId(), ct);',
              'FinSubsidyStandard std = resolveStandard(cmd.standardId(), ct, cmd.subsidyPeriod());', 1)
# 批量的自动匹配调用
s = s.replace('resolveStandard(null, ct)', 'resolveStandard(null, ct, subsidyPeriod)')
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('subsidy effective period fixed')

# ---------- 4) 折扣率范围校验 ----------
p = r'..\backend\src\main\java\com\yundao\bp\fin\service\BillingCalculator.java'
s = io.open(p, encoding='utf-8').read()
old = '''                BigDecimal rate = extractRate(config);
                if (rate != null) {'''
new = '''                BigDecimal rate = extractRate(config);
                if (rate != null && (rate.compareTo(BigDecimal.ZERO) < 0
                        || rate.compareTo(BigDecimal.ONE) > 0)) {
                    throw BizException.paramInvalid("折扣率应在 0~1 之间: " + rate);
                }
                if (rate != null) {'''
if old in s:
    s = s.replace(old, new, 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('discount rate validated')
