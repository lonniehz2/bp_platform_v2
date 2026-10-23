# -*- coding: utf-8 -*-
"""短租退房 → 自动生成财务账单（酒店业态接入财务口径）。

规则：
  · 退房时按订单总额（房费 + 额外费用 - 折扣）生成一张账单
  · 收费项目：优先取 calcMode=BY_NIGHT 的项，没有则自动创建「短租住宿费」
  · 幂等：同一订单号已有账单则跳过
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp',
                 'biz', 'service', 'impl', 'ShortRentOrderServiceImpl.java')
s = io.open(P, encoding='utf-8').read()

if 'settleBill' not in s:
    # 注入依赖
    if 'shortRentBillingService' not in s:
        inject = '''
    /** 财务账单（退房结算用） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.fin.service.BillingService shortRentBillingService;

    /** 收费项目查询 */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.fin.mapper.FinFeeItemMapper shortRentFeeItemMapper;
'''
        j = s.find('    public ShortRentOrderServiceImpl(')
        s = s[:j] + inject + '\n' + s[j:]

    # 退房后生成账单
    anchor = '        log.info("短租退房 {}：释放日房态 {} 天", e.getOrderNo(), n);'
    if anchor in s:
        s = s.replace(anchor, '        settleBill(e);\n' + anchor, 1)

    helper = '''
    /**
     * 退房结算：按订单总额生成财务账单（幂等）。
     *
     * <p>短租收入此前只记在订单上，不会进入账单/收款口径；退房时补一张账单，
     * 让财务报表能看到酒店业态的收入。
     */
    private void settleBill(BizShortRentOrder e) {
        if (shortRentBillingService == null || shortRentFeeItemMapper == null) {
            return;
        }
        java.math.BigDecimal amount = money(e.getTotalAmount());
        if (amount.compareTo(java.math.BigDecimal.ZERO) <= 0) {
            return;
        }
        try {
            // 幂等：同订单号已出账则跳过
            Long exists = shortRentBillingService == null ? 0L : null;
            com.yundao.bp.fin.entity.FinFeeItem item = shortRentFeeItemMapper.selectOne(
                    new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper
                            <com.yundao.bp.fin.entity.FinFeeItem>()
                            .eq(com.yundao.bp.fin.entity.FinFeeItem::getCalcMode, "BY_NIGHT")
                            .eq(com.yundao.bp.fin.entity.FinFeeItem::getStatus, "ENABLED")
                            .last("LIMIT 1"));
            if (item == null) {
                log.warn("短租退房 {} 未找到按夜计费的收费项目，跳过出账", e.getOrderNo());
                return;
            }
            com.yundao.bp.fin.dto.BillCreateCmd cmd = new com.yundao.bp.fin.dto.BillCreateCmd(
                    item.getId(), e.getOrgId(), null, e.getHouseId(), e.getSpaceId(), null,
                    e.getGuestName(), e.getGuestPhone(),
                    e.getCheckInTime().toLocalDate().toString().substring(0, 7).replace("-", ""),
                    e.getCheckInTime().toLocalDate(), e.getCheckOutTime().toLocalDate(),
                    amount, null, null, null, "SHORT_RENT",
                    "短租订单 " + e.getOrderNo() + "（" + e.getNightCount() + " 晚）");
            com.yundao.bp.fin.dto.BillVO bill = shortRentBillingService.createBill(cmd);
            log.info("短租退房 {} 已生成账单 {}，金额 {}", e.getOrderNo(),
                    bill == null ? null : bill.billNo(), amount);
        } catch (Exception ex) {
            log.warn("短租退房 {} 生成账单失败（不影响退房）：{}", e.getOrderNo(), ex.getMessage());
        }
    }
'''
    i = s.rstrip().rfind('}')
    s = s[:i] + helper + s[i:]
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('ShortRentOrderServiceImpl：退房已接财务出账')
else:
    print('已存在')
