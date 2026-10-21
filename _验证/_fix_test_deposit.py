# -*- coding: utf-8 -*-
"""修正押金测试：mock selectOne、退款金额必填、零余额语义"""
import io

p = (r'D:\Work\业务平台开发\backend\src\test\java\com\yundao\bp\fin'
     r'\DepositRefundTest.java')
s = io.open(p, encoding='utf-8').read()

# 1) "默认退全部余额" 不成立（实现要求金额必填）→ 改为显式金额
old1 = '''    @Test
    @DisplayName("⭐ 申请退款：默认退全部余额，状态 PENDING")
    void createRefundDefaultsToBalance() {
        when(depositMapper.selectById(1L))
                .thenReturn(deposit("2000", "2000", "0", "0", "HELD"));

        RefundVO vo = service.createRefund(new RefundCreateCmd(
                null, 4001L, 2001L, null, "DEPOSIT", "BANK", "退租结算"));
        assertEquals(0, new BigDecimal("2000").compareTo(vo.refundAmount()));
        assertEquals("PENDING", vo.refundStatus());
    }'''
new1 = '''    @Test
    @DisplayName("⭐ 申请退还押金：金额必填，状态 PENDING")
    void createRefund() {
        when(depositMapper.selectOne(any()))
                .thenReturn(deposit("2000", "2000", "0", "0", "HELD"));

        RefundVO vo = service.createRefund(new RefundCreateCmd(
                null, 4001L, 2001L, new BigDecimal("2000"), "DEPOSIT", "BANK",
                "退租结算"));
        assertEquals(0, new BigDecimal("2000").compareTo(vo.refundAmount()));
        assertEquals("PENDING", vo.refundStatus());
    }

    @Test
    @DisplayName("⭐ 退款金额不填 → 拒绝（不做隐式默认，避免误退）")
    void createRefundWithoutAmountRejected() {
        BizException ex = assertThrows(BizException.class,
                () -> service.createRefund(new RefundCreateCmd(
                        null, 4001L, 2001L, null, "DEPOSIT", "BANK", "x")));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
        assertTrue(ex.getMessage().contains("必须大于 0"), ex.getMessage());
    }'''
assert old1 in s
s = s.replace(old1, new1, 1)

# 2) 超额：mock selectOne
old2 = '''        when(depositMapper.selectById(1L))
                .thenReturn(deposit("2000", "2000", "0", "0", "HELD"));

        BizException ex = assertThrows(BizException.class,
                () -> service.createRefund(new RefundCreateCmd(
                        null, 4001L, 2001L, new BigDecimal("2500"), "DEPOSIT",
                        "BANK", "x")));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());'''
new2 = '''        when(depositMapper.selectOne(any()))
                .thenReturn(deposit("2000", "2000", "0", "0", "HELD"));

        BizException ex = assertThrows(BizException.class,
                () -> service.createRefund(new RefundCreateCmd(
                        null, 4001L, 2001L, new BigDecimal("2500"), "DEPOSIT",
                        "BANK", "x")));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
        assertTrue(ex.getMessage().contains("超过押金余额"), ex.getMessage());'''
assert old2 in s
s = s.replace(old2, new2, 1)

# 3) 零余额：语义是「超额」而非「无余额冲突」→ 断言 PARAM_INVALID
old3 = '''    @Test
    @DisplayName("⭐ 余额为 0（已全额抵扣）时不可申请退款")
    void refundNoBalance() {
        when(depositMapper.selectById(1L))
                .thenReturn(deposit("2000", "2000", "2000", "0", "DEDUCTED"));

        BizException ex = assertThrows(BizException.class,
                () -> service.createRefund(new RefundCreateCmd(
                        null, 4001L, 2001L, null, "DEPOSIT", "BANK", "x")));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }'''
new3 = '''    @Test
    @DisplayName("⭐⭐ 余额为 0（已全额抵扣）→ 任何退款都超过余额，被拒")
    void refundNoBalance() {
        when(depositMapper.selectOne(any()))
                .thenReturn(deposit("2000", "2000", "2000", "0", "DEDUCTED"));

        BizException ex = assertThrows(BizException.class,
                () -> service.createRefund(new RefundCreateCmd(
                        null, 4001L, 2001L, new BigDecimal("100"), "DEPOSIT",
                        "BANK", "x")));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
        assertTrue(ex.getMessage().contains("超过押金余额"), ex.getMessage());
    }

    @Test
    @DisplayName("⭐ 合同无押金台账 → 不可退押金")
    void refundWithoutDeposit() {
        when(depositMapper.selectOne(any())).thenReturn(null);
        BizException ex = assertThrows(BizException.class,
                () -> service.createRefund(new RefundCreateCmd(
                        null, 4001L, 2001L, new BigDecimal("100"), "DEPOSIT",
                        "BANK", "x")));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
        assertTrue(ex.getMessage().contains("无押金台账"), ex.getMessage());
    }'''
assert old3 in s
s = s.replace(old3, new3, 1)

# 4) 状态语义测试：completeRefund 走 selectOne
s = s.replace('''        FinDeposit d = deposit("2000", "2000", "300", "0", "HELD");
        when(depositMapper.selectById(1L)).thenReturn(d);''',
              '''        FinDeposit d = deposit("2000", "2000", "300", "0", "HELD");
        when(depositMapper.selectOne(any())).thenReturn(d);''', 1)

s = s.replace('''        FinDeposit d = deposit("2000", "2000", "0", "0", "HELD");
        when(depositMapper.selectById(1L)).thenReturn(d);
        when(refundMapper.selectById(9L)).thenReturn(refund("500", "APPROVED"));''',
              '''        FinDeposit d = deposit("2000", "2000", "0", "0", "HELD");
        when(depositMapper.selectOne(any())).thenReturn(d);
        when(refundMapper.selectById(9L)).thenReturn(refund("500", "APPROVED"));''', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('已修正 5 处：selectOne 打桩、金额必填、零余额语义、无台账场景')
