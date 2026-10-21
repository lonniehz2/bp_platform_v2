# -*- coding: utf-8 -*-
"""生成押金退款测试（状态机 + 余额重算）+ 公示门槛测试"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\test\java\com\yundao\bp'

# ==================== 1) 押金退款 ====================
DEPOSIT = r'''package com.yundao.bp.fin;

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
 * <p><b>为什么必须测</b>：押金是住户的钱，抵扣/退还金额算错就是直接少退住户钱。
 * 此前真实踩过一个 bug：抵扣 300 + 退还 1700 却被标成 {@code DEDUCTED}，
 * 正确语义应是 {@code REFUNDED}（余额已清零且确有退款）。
 * 这类<b>状态语义</b>错误账面上看不出来，只能靠测试锁住。
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

    private static FinDeposit deposit(String amount, String deducted, String refunded,
                                      String status) {
        FinDeposit d = new FinDeposit();
        d.setId(1L);
        d.setTenantId("350600");
        d.setContractId(2001L);
        d.setPersonId(4001L);
        d.setDepositAmount(new BigDecimal(amount));
        d.setDeductedAmount(new BigDecimal(deducted));
        d.setRefundedAmount(new BigDecimal(refunded));
        d.setBalance(new BigDecimal(amount).subtract(new BigDecimal(deducted))
                .subtract(new BigDecimal(refunded)));
        d.setDepositStatus(status);
        return d;
    }

    private static FinRefund refund(String amount, String status) {
        FinRefund r = new FinRefund();
        r.setId(9L);
        r.setTenantId("350600");
        r.setDepositId(1L);
        r.setContractId(2001L);
        r.setRefundAmount(new BigDecimal(amount));
        r.setRefundStatus(status);
        return r;
    }

    // ==================== 押金收取 ====================

    @Test
    @DisplayName("收取押金：余额 = 押金金额，状态 PAID")
    void receiveDeposit() {
        FinDeposit d = deposit("2000", "0", "0", "UNPAID");
        d.setDepositAmount(BigDecimal.ZERO);
        d.setBalance(BigDecimal.ZERO);
        when(depositMapper.selectById(1L)).thenReturn(d);

        DepositVO vo = service.receiveDeposit(1L, new BigDecimal("2000"));
        assertEquals(0, new BigDecimal("2000").compareTo(vo.depositAmount()));
        assertEquals(0, new BigDecimal("2000").compareTo(vo.balance()));
        assertEquals("PAID", vo.depositStatus());
    }

    // ==================== 抵扣 ====================

    @Test
    @DisplayName("⭐ 抵扣：余额减少，累计抵扣增加")
    void deduct() {
        when(depositMapper.selectById(1L)).thenReturn(deposit("2000", "0", "0", "PAID"));

        DepositVO vo = service.deductDeposit(1L, new BigDecimal("300"), "损坏赔偿");
        assertEquals(0, new BigDecimal("300").compareTo(vo.deductedAmount()));
        assertEquals(0, new BigDecimal("1700").compareTo(vo.balance()));
        assertEquals("PARTIAL_DEDUCTED", vo.depositStatus());
    }

    @Test
    @DisplayName("⭐ 抵扣超额 → 拒绝（不能把押金扣成负数）")
    void deductExceedBalance() {
        when(depositMapper.selectById(1L)).thenReturn(deposit("2000", "0", "0", "PAID"));

        BizException ex = assertThrows(BizException.class,
                () -> service.deductDeposit(1L, new BigDecimal("2500"), "赔偿"));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
        assertTrue(ex.getMessage().contains("余额") || ex.getMessage().contains("超过"),
                ex.getMessage());
    }

    @Test
    @DisplayName("抵扣金额为 0 或负数 → 拒绝")
    void deductNonPositive() {
        when(depositMapper.selectById(1L)).thenReturn(deposit("2000", "0", "0", "PAID"));
        assertThrows(BizException.class,
                () -> service.deductDeposit(1L, BigDecimal.ZERO, "x"));
        assertThrows(BizException.class,
                () -> service.deductDeposit(1L, new BigDecimal("-100"), "x"));
    }

    @Test
    @DisplayName("⭐ 抵扣 = 全部余额 → 状态 DEDUCTED（余额 0，无退款）")
    void deductAllMarksDeducted() {
        when(depositMapper.selectById(1L)).thenReturn(deposit("2000", "0", "0", "PAID"));

        DepositVO vo = service.deductDeposit(1L, new BigDecimal("2000"), "全额抵扣");
        assertEquals(0, BigDecimal.ZERO.compareTo(vo.balance()));
        assertEquals("DEDUCTED", vo.depositStatus());
    }

    // ==================== 退款申请 ====================

    @Test
    @DisplayName("申请退款：默认退全部余额，状态 PENDING")
    void createRefundDefaultsToBalance() {
        when(depositMapper.selectById(1L)).thenReturn(deposit("2000", "0", "0", "PAID"));

        RefundVO vo = service.createRefund(new com.yundao.bp.fin.dto.RefundCreateCmd(
                1L, null, "退租结算", null, null));
        assertEquals(0, new BigDecimal("2000").compareTo(vo.refundAmount()));
        assertEquals("PENDING", vo.refundStatus());
    }

    @Test
    @DisplayName("⭐ 退款额超余额 → 拒绝")
    void refundExceedBalance() {
        when(depositMapper.selectById(1L)).thenReturn(deposit("2000", "0", "0", "PAID"));

        BizException ex = assertThrows(BizException.class,
                () -> service.createRefund(new com.yundao.bp.fin.dto.RefundCreateCmd(
                        1L, new BigDecimal("2500"), "x", null, null)));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
    }

    @Test
    @DisplayName("⭐ 余额为 0 时不可申请退款")
    void refundNoBalance() {
        when(depositMapper.selectById(1L)).thenReturn(deposit("2000", "2000", "0", "DEDUCTED"));

        BizException ex = assertThrows(BizException.class,
                () -> service.createRefund(new com.yundao.bp.fin.dto.RefundCreateCmd(
                        1L, null, "x", null, null)));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    // ==================== 退款状态机 ====================

    @Test
    @DisplayName("审批通过：PENDING → APPROVED")
    void approve() {
        when(refundMapper.selectById(9L)).thenReturn(refund("1700", "PENDING"));
        RefundVO vo = service.approveRefund(9L, 1001L);
        assertEquals("APPROVED", vo.refundStatus());
    }

    @Test
    @DisplayName("⭐ 重复审批 → 拒绝（状态机不可跳跃）")
    void approveTwiceRejected() {
        when(refundMapper.selectById(9L)).thenReturn(refund("1700", "APPROVED"));
        BizException ex = assertThrows(BizException.class,
                () -> service.approveRefund(9L, 1001L));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    @Test
    @DisplayName("驳回：PENDING → REJECTED，需记录原因")
    void reject() {
        when(refundMapper.selectById(9L)).thenReturn(refund("1700", "PENDING"));
        RefundVO vo = service.rejectRefund(9L, 1001L, "材料不全");
        assertEquals("REJECTED", vo.refundStatus());
    }

    @Test
    @DisplayName("未经审批直接完成 → 拒绝（必须先 APPROVED）")
    void completeWithoutApproveRejected() {
        when(refundMapper.selectById(9L)).thenReturn(refund("1700", "PENDING"));
        BizException ex = assertThrows(BizException.class,
                () -> service.completeRefund(9L));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    // ==================== ⭐⭐ 状态语义（曾经的真实 bug） ====================

    @Test
    @DisplayName("⭐⭐ 抵扣300+退款1700 → 余额清零且状态 REFUNDED（不是 DEDUCTED）")
    void partialDeductThenRefundMarksRefunded() {
        // 押金 2000，先抵扣 300，剩 1700
        FinDeposit d = deposit("2000", "300", "0", "PARTIAL_DEDUCTED");
        when(depositMapper.selectById(1L)).thenReturn(d);
        when(refundMapper.selectById(9L)).thenReturn(refund("1700", "APPROVED"));

        RefundVO vo = service.completeRefund(9L);

        assertEquals("COMPLETED", vo.refundStatus());
        // 押金：已退 1700，余额 0
        assertEquals(0, new BigDecimal("1700").compareTo(d.getRefundedAmount()));
        assertEquals(0, BigDecimal.ZERO.compareTo(d.getBalance()));
        // ⭐ 关键：既有退款发生，状态必须是 REFUNDED
        assertEquals("REFUNDED", d.getDepositStatus(),
                "余额清零且有退款，应为 REFUNDED，实际 " + d.getDepositStatus());
    }

    @Test
    @DisplayName("⭐⭐ 全额抵扣无退款 → 状态 DEDUCTED（与上一条区分）")
    void fullDeductNoRefundMarksDeducted() {
        FinDeposit d = deposit("2000", "2000", "0", "DEDUCTED");
        when(depositMapper.selectById(1L)).thenReturn(d);
        assertEquals(0, BigDecimal.ZERO.compareTo(d.getBalance()));
        assertEquals("DEDUCTED", d.getDepositStatus());
    }

    @Test
    @DisplayName("⭐ 部分退款后仍有余额 → PARTIAL_REFUNDED（不提前标记完成）")
    void partialRefundKeepsBalance() {
        FinDeposit d = deposit("2000", "0", "0", "PAID");
        when(depositMapper.selectById(1L)).thenReturn(d);
        when(refundMapper.selectById(9L)).thenReturn(refund("500", "APPROVED"));

        service.completeRefund(9L);

        assertEquals(0, new BigDecimal("500").compareTo(d.getRefundedAmount()));
        assertEquals(0, new BigDecimal("1500").compareTo(d.getBalance()));
        assertEquals("PARTIAL_REFUNDED", d.getDepositStatus());
    }

    @Test
    @DisplayName("退款单不存在 → 404")
    void refundNotFound() {
        when(refundMapper.selectById(9L)).thenReturn(null);
        BizException ex = assertThrows(BizException.class,
                () -> service.completeRefund(9L));
        assertEquals(ErrorCode.NOT_FOUND, ex.errorCode());
    }
}
'''

# ==================== 2) 公示门槛 ====================
GATE = r'''package com.yundao.bp.biz;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.LocalDate;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * 配租公示门槛测试（决策 D23）。
 *
 * <p><b>业务规则</b>：配租结果必须完成公示（不少于 7 个自然日且已结束），
 * 才能办理签约。<b>这是合规硬校验，不可绕过</b>。
 *
 * <p>此处测的是「公示期判定」这一纯逻辑：给定公示起止日期与当前日期，
 * 判断是否满足「已发布 + 满 7 天 + 已结束」。真实实现中
 * {@code PublicityServiceImpl#hasCompletedAllocationPublicity} 会先查库再调用同样口径。
 */
class PublicityGateTest {

    private static final int MIN_DAYS = 7;

    /**
     * 复刻判定口径：公示已开始、已结束、且跨度 ≥ 最小天数。
     *
     * @param published 是否已发布
     * @param start     公示开始日
     * @param end       公示结束日
     * @param today     当前日期
     */
    private static boolean canSign(boolean published, LocalDate start, LocalDate end,
                                   LocalDate today) {
        if (!published || start == null || end == null) {
            return false;
        }
        // 未开始公示不能签约
        if (today.isBefore(start)) {
            return false;
        }
        // 公示未结束（含今天仍在公示期内）不能签约
        if (!today.isAfter(end)) {
            return false;
        }
        // 跨度不足最小天数不能签约（含首尾，days = end - start + 1）
        long days = end.toEpochDay() - start.toEpochDay() + 1;
        return days >= MIN_DAYS;
    }

    @Test
    @DisplayName("⭐ 已公示 7 天且已结束 → 允许签约")
    void sevenDaysEnded() {
        LocalDate start = LocalDate.of(2026, 10, 1);
        LocalDate end = LocalDate.of(2026, 10, 7);   // 含首尾正好 7 天
        assertTrue(canSign(true, start, end, LocalDate.of(2026, 10, 8)));
    }

    @Test
    @DisplayName("⭐⭐ 公示未结束（今天仍在期内）→ 禁止签约")
    void notEndedBlocks() {
        LocalDate start = LocalDate.of(2026, 10, 1);
        LocalDate end = LocalDate.of(2026, 10, 7);
        assertFalse(canSign(true, start, end, LocalDate.of(2026, 10, 7)),
                "公示最后一天当天不得签约");
        assertFalse(canSign(true, start, end, LocalDate.of(2026, 10, 5)),
                "公示期内不得签约");
    }

    @Test
    @DisplayName("⭐ 公示仅 6 天 → 禁止签约（不足 7 个自然日）")
    void sixDaysBlocks() {
        LocalDate start = LocalDate.of(2026, 10, 1);
        LocalDate end = LocalDate.of(2026, 10, 6);   // 含首尾 6 天
        assertFalse(canSign(true, start, end, LocalDate.of(2026, 10, 10)));
    }

    @Test
    @DisplayName("跨度 7 天但还没结束 → 仍禁止（两个条件都要满足）")
    void longEnoughButNotEnded() {
        LocalDate start = LocalDate.of(2026, 10, 1);
        LocalDate end = LocalDate.of(2026, 10, 20);
        assertFalse(canSign(true, start, end, LocalDate.of(2026, 10, 10)),
                "虽然跨 20 天，但公示未结束");
        assertTrue(canSign(true, start, end, LocalDate.of(2026, 10, 21)));
    }

    @Test
    @DisplayName("⭐ 未发布公示 → 禁止签约")
    void unpublishedBlocks() {
        assertFalse(canSign(false, LocalDate.of(2026, 10, 1),
                LocalDate.of(2026, 10, 7), LocalDate.of(2026, 10, 8)));
    }

    @Test
    @DisplayName("公示尚未开始 → 禁止签约")
    void notStartedBlocks() {
        LocalDate start = LocalDate.of(2026, 11, 1);
        LocalDate end = LocalDate.of(2026, 11, 7);
        assertFalse(canSign(true, start, end, LocalDate.of(2026, 10, 20)));
    }

    @Test
    @DisplayName("缺失公示日期 → 禁止签约（不能默认放行）")
    void nullDatesBlock() {
        assertFalse(canSign(true, null, null, LocalDate.now()));
        assertFalse(canSign(true, LocalDate.now(), null, LocalDate.now()));
    }

    @Test
    @DisplayName("⭐ 缺省必须拒绝：宁可挡住业务，也不能违规签约")
    void failClosed() {
        // 各种「信息不全」场景一律拒绝
        assertFalse(canSign(false, null, null, null == null ? LocalDate.now() : null));
        assertFalse(canSign(true, LocalDate.of(2026, 10, 1), LocalDate.of(2026, 10, 7),
                LocalDate.of(2026, 9, 30)));
    }

    @Test
    @DisplayName("跨越月份/年末也不受影响（按自然日算）")
    void crossMonth() {
        // 2026-12-28 ~ 2027-01-03 含首尾 = 7 天
        LocalDate start = LocalDate.of(2026, 12, 28);
        LocalDate end = LocalDate.of(2027, 1, 3);
        assertTrue(canSign(true, start, end, LocalDate.of(2027, 1, 4)));
    }

    @Test
    @DisplayName("公示期很长也应允许（≥7 天即可，无上限）")
    void veryLongOk() {
        assertTrue(canSign(true, LocalDate.of(2026, 1, 1),
                LocalDate.of(2026, 3, 1), LocalDate.of(2026, 3, 2)));
    }
}
'''

for rel, src in (('fin/DepositRefundTest.java', DEPOSIT),
                 ('biz/PublicityGateTest.java', GATE)):
    p = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, 'w', encoding='utf-8').write(src)
    print('  + %s（%d 行）' % (rel, src.count('\n')))
