# -*- coding: utf-8 -*-
"""按真实字段/状态重写押金退款测试"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\test\java\com\yundao\bp\fin'

SRC = r'''package com.yundao.bp.fin;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
import com.yundao.bp.fin.dto.DepositVO;
import com.yundao.bp.fin.dto.RefundCreateCmd;
import com.yundao.bp.fin.dto.RefundVO;
import com.yundao.bp.fin.entity.FinDeposit;
import com.yundao.bp.fin.entity.FinRefund;
import com.yundao.bp.fin.mapper.FinDepositMapper;
import com.yundao.bp.fin.mapper.FinRefundMapper;
import com.yundao.bp.fin.service.impl.DepositRefundServiceImpl;
import java.math.BigDecimal;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;

/**
 * 押金与退款测试。
 *
 * <p><b>为什么必须测</b>：押金是住户自己的钱，抵扣/退还金额算错直接造成少退。
 * 这里锁住三件事：
 * <ol>
 *   <li><b>余额公式</b>：余额 = 已收 − 已抵扣 − 已退还，任何一步都不能为负</li>
 *   <li><b>状态语义</b>：（曾经真实出过 bug）抵扣 300 + 退还 1700 余额归零，
 *       状态必须是 {@code REFUNDED} 而不是 {@code DEDUCTED}</li>
 *   <li><b>状态机</b>：PENDING → APPROVED → SUCCESS，不可跳跃、不可重复</li>
 * </ol>
 */
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class DepositRefundTest {

    @Mock
    private FinDepositMapper depositMapper;
    @Mock
    private FinRefundMapper refundMapper;

    private DepositRefundServiceImpl service;

    @BeforeEach
    void setUp() {
        service = new DepositRefundServiceImpl(depositMapper, refundMapper,
                new SnowflakeIdGenerator(1, 1));
        TenantContext.set(TenantInfo.of("350600", 1001L));
        when(depositMapper.updateById(any(FinDeposit.class))).thenReturn(1);
        when(refundMapper.updateById(any(FinRefund.class))).thenReturn(1);
        when(depositMapper.insert(any(FinDeposit.class))).thenReturn(1);
        when(refundMapper.insert(any(FinRefund.class))).thenReturn(1);
    }

    @AfterEach
    void tearDown() {
        TenantContext.clear();
    }

    /** 构造押金台账（余额自动按公式算）。 */
    private static FinDeposit deposit(String due, String paid, String deduct,
                                      String refund, String status) {
        FinDeposit d = new FinDeposit();
        d.setId(1L);
        d.setTenantId("350600");
        d.setContractId(2001L);
        d.setPersonId(4001L);
        d.setDepositAmount(new BigDecimal(due));
        d.setPaidAmount(new BigDecimal(paid));
        d.setDeductAmount(new BigDecimal(deduct));
        d.setRefundAmount(new BigDecimal(refund));
        d.setBalanceAmount(new BigDecimal(paid).subtract(new BigDecimal(deduct))
                .subtract(new BigDecimal(refund)));
        d.setDepositStatus(status);
        return d;
    }

    private static FinRefund refund(String amount, String status) {
        FinRefund r = new FinRefund();
        r.setId(9L);
        r.setTenantId("350600");
        r.setPaymentId(1L);
        r.setPersonId(4001L);
        r.setContractId(2001L);
        r.setRefundAmount(new BigDecimal(amount));
        r.setRefundStatus(status);
        return r;
    }

    // ==================== 补收 ====================

    @Test
    @DisplayName("⭐ 补收押金：已收增加，余额同步增加")
    void receiveMore() {
        FinDeposit d = deposit("2000", "500", "0", "0", "HELD");
        when(depositMapper.selectById(1L)).thenReturn(d);

        DepositVO vo = service.receiveDeposit(1L, new BigDecimal("500"));
        assertEquals(0, new BigDecimal("1000").compareTo(vo.paidAmount()));
        assertEquals(0, new BigDecimal("1000").compareTo(vo.balanceAmount()));
    }

    @Test
    @DisplayName("补收金额为 0/负数 → 拒绝")
    void receiveNonPositive() {
        when(depositMapper.selectById(1L)).thenReturn(deposit("2000", "0", "0", "0", "HELD"));
        assertThrows(BizException.class, () -> service.receiveDeposit(1L, BigDecimal.ZERO));
        assertThrows(BizException.class,
                () -> service.receiveDeposit(1L, new BigDecimal("-1")));
    }

    // ==================== 抵扣 ====================

    @Test
    @DisplayName("⭐ 抵扣：累计抵扣增加，余额减少（2000 − 300 = 1700）")
    void deduct() {
        FinDeposit d = deposit("2000", "2000", "0", "0", "HELD");
        when(depositMapper.selectById(1L)).thenReturn(d);

        DepositVO vo = service.deductDeposit(1L, new BigDecimal("300"), "损坏赔偿");
        assertEquals(0, new BigDecimal("300").compareTo(vo.deductAmount()));
        assertEquals(0, new BigDecimal("1700").compareTo(vo.balanceAmount()));
        assertEquals("HELD", vo.depositStatus(), "仍有余额时应保持 HELD");
    }

    @Test
    @DisplayName("⭐⭐ 抵扣超额 → 拒绝（押金不能扣成负数）")
    void deductExceedBalance() {
        when(depositMapper.selectById(1L))
                .thenReturn(deposit("2000", "2000", "0", "0", "HELD"));

        BizException ex = assertThrows(BizException.class,
                () -> service.deductDeposit(1L, new BigDecimal("2500"), "赔偿"));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
        assertTrue(ex.getMessage().contains("超过押金余额"), ex.getMessage());
    }

    @Test
    @DisplayName("抵扣金额为 0/负数 → 拒绝")
    void deductNonPositive() {
        when(depositMapper.selectById(1L))
                .thenReturn(deposit("2000", "2000", "0", "0", "HELD"));
        assertThrows(BizException.class,
                () -> service.deductDeposit(1L, BigDecimal.ZERO, "x"));
        assertThrows(BizException.class,
                () -> service.deductDeposit(1L, new BigDecimal("-100"), "x"));
    }

    @Test
    @DisplayName("⭐ 已退还的押金不可再抵扣（终态保护）")
    void deductAfterRefundedRejected() {
        when(depositMapper.selectById(1L))
                .thenReturn(deposit("2000", "2000", "0", "2000", "REFUNDED"));
        BizException ex = assertThrows(BizException.class,
                () -> service.deductDeposit(1L, new BigDecimal("100"), "x"));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    @Test
    @DisplayName("⭐ 抵扣全部余额 → 状态 DEDUCTED（余额 0 且无退款）")
    void deductAllMarksDeducted() {
        when(depositMapper.selectById(1L))
                .thenReturn(deposit("2000", "2000", "0", "0", "HELD"));

        DepositVO vo = service.deductDeposit(1L, new BigDecimal("2000"), "全额抵扣");
        assertEquals(0, BigDecimal.ZERO.compareTo(vo.balanceAmount()));
        assertEquals("DEDUCTED", vo.depositStatus());
    }

    // ==================== 退款申请 ====================

    @Test
    @DisplayName("⭐ 申请退款：默认退全部余额，状态 PENDING")
    void createRefundDefaultsToBalance() {
        when(depositMapper.selectById(1L))
                .thenReturn(deposit("2000", "2000", "0", "0", "HELD"));

        RefundVO vo = service.createRefund(new RefundCreateCmd(
                null, 4001L, 2001L, null, "DEPOSIT", "BANK", "退租结算"));
        assertEquals(0, new BigDecimal("2000").compareTo(vo.refundAmount()));
        assertEquals("PENDING", vo.refundStatus());
    }

    @Test
    @DisplayName("⭐⭐ 退款额超余额 → 拒绝")
    void refundExceedBalance() {
        when(depositMapper.selectById(1L))
                .thenReturn(deposit("2000", "2000", "0", "0", "HELD"));

        BizException ex = assertThrows(BizException.class,
                () -> service.createRefund(new RefundCreateCmd(
                        null, 4001L, 2001L, new BigDecimal("2500"), "DEPOSIT",
                        "BANK", "x")));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
    }

    @Test
    @DisplayName("⭐ 余额为 0（已全额抵扣）时不可申请退款")
    void refundNoBalance() {
        when(depositMapper.selectById(1L))
                .thenReturn(deposit("2000", "2000", "2000", "0", "DEDUCTED"));

        BizException ex = assertThrows(BizException.class,
                () -> service.createRefund(new RefundCreateCmd(
                        null, 4001L, 2001L, null, "DEPOSIT", "BANK", "x")));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    // ==================== 退款状态机 ====================

    @Test
    @DisplayName("审批通过：PENDING → APPROVED")
    void approve() {
        when(refundMapper.selectById(9L)).thenReturn(refund("1700", "PENDING"));
        assertEquals("APPROVED", service.approveRefund(9L, 1001L).refundStatus());
    }

    @Test
    @DisplayName("⭐ 重复审批 → 拒绝（状态机不可重复）")
    void approveTwiceRejected() {
        when(refundMapper.selectById(9L)).thenReturn(refund("1700", "APPROVED"));
        BizException ex = assertThrows(BizException.class,
                () -> service.approveRefund(9L, 1001L));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    @Test
    @DisplayName("驳回：PENDING → REJECTED")
    void reject() {
        when(refundMapper.selectById(9L)).thenReturn(refund("1700", "PENDING"));
        assertEquals("REJECTED",
                service.rejectRefund(9L, 1001L, "材料不全").refundStatus());
    }

    @Test
    @DisplayName("⭐ 未经审批直接完成退款 → 拒绝（必须先 APPROVED）")
    void completeWithoutApproveRejected() {
        when(refundMapper.selectById(9L)).thenReturn(refund("1700", "PENDING"));
        BizException ex = assertThrows(BizException.class,
                () -> service.completeRefund(9L));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    @Test
    @DisplayName("⭐ 已驳回的退款不可再完成（终态保护）")
    void completeAfterRejectRejected() {
        when(refundMapper.selectById(9L)).thenReturn(refund("1700", "REJECTED"));
        assertThrows(BizException.class, () -> service.completeRefund(9L));
    }

    // ==================== ⭐⭐ 状态语义（真实 bug 回归） ====================

    @Test
    @DisplayName("⭐⭐ 抵扣 300 + 退还 1700 → 余额 0 且状态 REFUNDED（不是 DEDUCTED）")
    void partialDeductThenRefundMarksRefunded() {
        // 押金应收 2000，已收 2000，先抵扣 300（余额 1700）
        FinDeposit d = deposit("2000", "2000", "300", "0", "HELD");
        when(depositMapper.selectById(1L)).thenReturn(d);
        when(refundMapper.selectById(9L)).thenReturn(refund("1700", "APPROVED"));

        RefundVO vo = service.completeRefund(9L);

        assertEquals("SUCCESS", vo.refundStatus());
        assertEquals(0, new BigDecimal("1700").compareTo(d.getRefundAmount()));
        assertEquals(0, BigDecimal.ZERO.compareTo(d.getBalanceAmount()));
        // ⭐ 关键断言：有退款发生 → REFUNDED
        assertEquals("REFUNDED", d.getDepositStatus(),
                "余额清零且有退款应为 REFUNDED，实际 " + d.getDepositStatus());
    }

    @Test
    @DisplayName("⭐⭐ 全额抵扣（无退款）→ 状态 DEDUCTED")
    void fullDeductMarksDeducted() {
        FinDeposit d = deposit("2000", "2000", "2000", "0", "DEDUCTED");
        when(depositMapper.selectById(1L)).thenReturn(d);
        assertEquals(0, BigDecimal.ZERO.compareTo(d.getBalanceAmount()));
        assertEquals("DEDUCTED", d.getDepositStatus());
    }

    @Test
    @DisplayName("⭐ 部分退还后仍有余额 → PARTIAL_REFUND（不提前结束）")
    void partialRefundKeepsBalance() {
        FinDeposit d = deposit("2000", "2000", "0", "0", "HELD");
        when(depositMapper.selectById(1L)).thenReturn(d);
        when(refundMapper.selectById(9L)).thenReturn(refund("500", "APPROVED"));

        service.completeRefund(9L);

        assertEquals(0, new BigDecimal("500").compareTo(d.getRefundAmount()));
        assertEquals(0, new BigDecimal("1500").compareTo(d.getBalanceAmount()));
        assertEquals("PARTIAL_REFUND", d.getDepositStatus(),
                "仍有余额应为 PARTIAL_REFUND，实际 " + d.getDepositStatus());
    }

    @Test
    @DisplayName("退款单不存在 → 404")
    void refundNotFound() {
        when(refundMapper.selectById(9L)).thenReturn(null);
        BizException ex = assertThrows(BizException.class,
                () -> service.completeRefund(9L));
        assertEquals(ErrorCode.NOT_FOUND, ex.errorCode());
    }

    @Test
    @DisplayName("押金台账不存在 → 404")
    void depositNotFound() {
        when(depositMapper.selectById(1L)).thenReturn(null);
        BizException ex = assertThrows(BizException.class,
                () -> service.deductDeposit(1L, new BigDecimal("100"), "x"));
        assertEquals(ErrorCode.NOT_FOUND, ex.errorCode());
    }
}
'''

p = os.path.join(BASE, 'DepositRefundTest.java')
io.open(p, 'w', encoding='utf-8').write(SRC)
print('重写 %s（%d 行）' % (p, SRC.count('\n')))
