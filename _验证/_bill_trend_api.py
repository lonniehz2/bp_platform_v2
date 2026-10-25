# -*- coding: utf-8 -*-
"""账单趋势接口：近 N 个月 应收 / 实收 / 收缴率。

供「账单与缴费」与「运营驾驶舱」画趋势图。
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
F = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'fin')

C = os.path.join(F, 'controller', 'BillingController.java')
s = io.open(C, encoding='utf-8').read()

if '/bills/trend' not in s:
    block = '''
    /**
     * 账单趋势：近 N 个月的应收 / 实收 / 收缴率。
     *
     * <p>按账单所属账期（billPeriod，形如 2026-10）统计；
     * 实收取 paidAmount 合计，收缴率 = 实收 / 应收。
     */
    @com.yundao.bp.iam.security.RequirePerm("fin:bill:view")
    @GetMapping("/bills/trend")
    public R<java.util.List<java.util.Map<String, Object>>> billTrend(
            @RequestParam(defaultValue = "6") int months) {
        int window = Math.max(1, Math.min(months, 24));
        java.time.YearMonth end = java.time.YearMonth.now();
        java.util.List<java.util.Map<String, Object>> out = new java.util.ArrayList<>();
        for (int i = window - 1; i >= 0; i--) {
            java.time.YearMonth ym = end.minusMonths(i);
            String period = ym.toString();
            java.util.List<com.yundao.bp.fin.entity.FinBill> list =
                    billingService.listByPeriod(period);
            java.math.BigDecimal receivable = java.math.BigDecimal.ZERO;
            java.math.BigDecimal received = java.math.BigDecimal.ZERO;
            for (com.yundao.bp.fin.entity.FinBill b : list) {
                if (b.getPayableAmount() != null) {
                    receivable = receivable.add(b.getPayableAmount());
                }
                if (b.getPaidAmount() != null) {
                    received = received.add(b.getPaidAmount());
                }
            }
            java.util.Map<String, Object> m = new java.util.LinkedHashMap<>();
            m.put("month", period);
            m.put("receivable", receivable.setScale(2, java.math.RoundingMode.HALF_UP));
            m.put("received", received.setScale(2, java.math.RoundingMode.HALF_UP));
            m.put("bills", list.size());
            m.put("rate", receivable.signum() == 0 ? 0
                    : received.multiply(java.math.BigDecimal.valueOf(100))
                            .divide(receivable, 1, java.math.RoundingMode.HALF_UP));
            out.add(m);
        }
        return R.ok(out);
    }
'''
    anchor = '    @GetMapping("/payments/{id}")'
    s = s.replace(anchor, block + '\n' + anchor, 1)
    io.open(C, 'w', encoding='utf-8', newline='').write(s)
    print('BillingController：已加 /bills/trend')

# 服务接口 + 实现
S = os.path.join(F, 'service', 'BillingService.java')
s = io.open(S, encoding='utf-8').read()
if 'listByPeriod' not in s:
    i = s.rstrip().rfind('}')
    s = s[:i] + '''
    /** 按账期（yyyy-MM）取账单，供趋势统计。 */
    java.util.List<com.yundao.bp.fin.entity.FinBill> listByPeriod(String period);
''' + s[i:]
    io.open(S, 'w', encoding='utf-8', newline='').write(s)
    print('BillingService：已加 listByPeriod')

I = os.path.join(F, 'service', 'impl', 'BillingServiceImpl.java')
s = io.open(I, encoding='utf-8').read()
if 'listByPeriod' not in s:
    i = s.rstrip().rfind('}')
    s = s[:i] + '''
    @Override
    public java.util.List<com.yundao.bp.fin.entity.FinBill> listByPeriod(String period) {
        if (period == null || period.isBlank()) {
            return java.util.List.of();
        }
        return billMapper.selectList(new LambdaQueryWrapper<com.yundao.bp.fin.entity.FinBill>()
                .eq(com.yundao.bp.fin.entity.FinBill::getBillPeriod, period));
    }
''' + s[i:]
    io.open(I, 'w', encoding='utf-8', newline='').write(s)
    print('BillingServiceImpl：已加 listByPeriod')
