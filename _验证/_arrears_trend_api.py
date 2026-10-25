# -*- coding: utf-8 -*-
"""欠费趋势接口：近 N 月 逾期金额 / 逾期账单数 / 催缴动作数。

供「催缴管理」页画趋势图。
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
F = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'fin')

C = os.path.join(F, 'controller', 'ArrearsActionController.java')
s = io.open(C, encoding='utf-8').read()

if '/trend' not in s:
    block = '''
    /**
     * 欠费趋势：近 N 个月逾期金额、逾期账单数、催缴动作数。
     *
     * <p>逾期口径：账单状态为 OVERDUE 或已过期仍未缴清的账单，
     * 按账单所属账期（yyyy-MM 或 yyyyMM）归月。
     */
    @com.yundao.bp.iam.security.RequirePerm("fin:bill:view")
    @GetMapping("/trend")
    public R<java.util.List<java.util.Map<String, Object>>> trend(
            @RequestParam(defaultValue = "6") int months) {
        int window = Math.max(1, Math.min(months, 24));
        java.time.YearMonth end = java.time.YearMonth.now();
        java.util.List<java.util.Map<String, Object>> out = new java.util.ArrayList<>();
        for (int i = window - 1; i >= 0; i--) {
            java.time.YearMonth ym = end.minusMonths(i);
            String period = ym.toString();
            java.util.List<com.yundao.bp.fin.entity.FinBill> bills =
                    billingService.listByPeriod(period);
            java.math.BigDecimal overdue = java.math.BigDecimal.ZERO;
            int overdueCount = 0;
            for (com.yundao.bp.fin.entity.FinBill b : bills) {
                boolean isOverdue = "OVERDUE".equals(b.getBillStatus())
                        || (("UNPAID".equals(b.getBillStatus())
                                || "PARTIAL".equals(b.getBillStatus()))
                            && b.getDueDate() != null
                            && b.getDueDate().isBefore(java.time.LocalDate.now()));
                if (!isOverdue) {
                    continue;
                }
                overdueCount++;
                java.math.BigDecimal pending = b.getPayableAmount() == null
                        ? java.math.BigDecimal.ZERO : b.getPayableAmount();
                if (b.getPaidAmount() != null) {
                    pending = pending.subtract(b.getPaidAmount());
                }
                if (pending.signum() > 0) {
                    overdue = overdue.add(pending);
                }
            }
            long actions = billingService.countArrearsActions(period);
            java.util.Map<String, Object> m = new java.util.LinkedHashMap<>();
            m.put("month", period);
            m.put("overdueAmount", overdue.setScale(2, java.math.RoundingMode.HALF_UP));
            m.put("overdueBills", overdueCount);
            m.put("actions", actions);
            out.add(m);
        }
        return R.ok(out);
    }
'''
    anchor = '    @GetMapping("/by-contract/{contractId}")'
    s = s.replace(anchor, block + '\n' + anchor, 1)
    io.open(C, 'w', encoding='utf-8', newline='').write(s)
    print('ArrearsActionController：已加 /trend')

# 服务接口
S = os.path.join(F, 'service', 'BillingService.java')
s = io.open(S, encoding='utf-8').read()
if 'countArrearsActions' not in s:
    i = s.rstrip().rfind('}')
    s = s[:i] + '''
    /** 按账期统计催缴动作数（趋势用）。 */
    long countArrearsActions(String period);
''' + s[i:]
    io.open(S, 'w', encoding='utf-8', newline='').write(s)
    print('BillingService：已加 countArrearsActions')

# 实现
I = os.path.join(F, 'service', 'impl', 'BillingServiceImpl.java')
s = io.open(I, encoding='utf-8').read()
if 'countArrearsActions' not in s:
    i = s.rstrip().rfind('}')
    s = s[:i] + '''
    @Override
    public long countArrearsActions(String period) {
        if (period == null || period.isBlank() || arrearsActionMapper == null) {
            return 0L;
        }
        java.time.LocalDate start = java.time.YearMonth.parse(period).atDay(1);
        java.time.LocalDate stop = start.plusMonths(1);
        Long n = arrearsActionMapper.selectCount(
                new LambdaQueryWrapper<com.yundao.bp.fin.entity.FinArrearsAction>()
                        .ge(com.yundao.bp.fin.entity.FinArrearsAction::getCreateTime,
                                start.atStartOfDay())
                        .lt(com.yundao.bp.fin.entity.FinArrearsAction::getCreateTime,
                                stop.atStartOfDay()));
        return n == null ? 0L : n;
    }
''' + s[i:]
    # 注入 mapper
    if 'arrearsActionMapper' in s and 'private com.yundao.bp.fin.mapper.FinArrearsActionMapper' not in s:
        pass
    s = s.replace('''    private final FinBillMapper billMapper;''','''    private final FinBillMapper billMapper;

    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.fin.mapper.FinArrearsActionMapper arrearsActionMapper;''', 1)
    io.open(I, 'w', encoding='utf-8', newline='').write(s)
    print('BillingServiceImpl：已加 countArrearsActions')
