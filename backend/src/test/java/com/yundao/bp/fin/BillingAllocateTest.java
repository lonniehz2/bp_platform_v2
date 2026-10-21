package com.yundao.bp.fin;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
import com.yundao.bp.fin.dto.BillVO;
import com.yundao.bp.fin.entity.FinBill;
import com.yundao.bp.fin.entity.FinPayment;
import com.yundao.bp.fin.entity.FinPaymentAllocate;
import com.yundao.bp.fin.mapper.FinBillMapper;
import com.yundao.bp.fin.mapper.FinPaymentAllocateMapper;
import com.yundao.bp.fin.mapper.FinPaymentMapper;
import com.yundao.bp.fin.service.impl.BillingServiceImpl;
import java.math.BigDecimal;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;

/**
 * 收款核销测试。
 *
 * <p><b>核心是三重上限</b>：核销额不能超过「收款单余额」「账单应付」，
 * 且已缴账单不可再核销。任意一条失守就是资金账实不符。
 */
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class BillingAllocateTest {

    @Mock
    private FinBillMapper billMapper;
    @Mock
    private FinPaymentMapper paymentMapper;
    @Mock
    private FinPaymentAllocateMapper allocateMapper;

    private BillingServiceImpl service;

    @BeforeEach
    void setUp() {
        service = new BillingServiceImpl(billMapper, paymentMapper, allocateMapper,
                new SnowflakeIdGenerator(1, 1));
        TenantContext.set(TenantInfo.of("350600", 1001L));
        when(allocateMapper.insert(any(FinPaymentAllocate.class))).thenReturn(1);
        when(billMapper.updateById(any(FinBill.class))).thenReturn(1);
        when(paymentMapper.updateById(any(FinPayment.class))).thenReturn(1);
    }

    @AfterEach
    void tearDown() {
        TenantContext.clear();
    }

    private static FinPayment payment(long id, String amount, String reconciled) {
        FinPayment p = new FinPayment();
        p.setId(id);
        p.setTenantId("350600");
        p.setPaymentNo("FP" + id);
        p.setPayAmount(new BigDecimal(amount));
        p.setReconciledAmount(new BigDecimal(reconciled));
        p.setPayStatus("SUCCESS");
        p.setReconcileStatus("UNRECONCILED");
        return p;
    }

    private static FinBill bill(long id, String payable, String paid, String status) {
        FinBill b = new FinBill();
        b.setId(id);
        b.setTenantId("350600");
        b.setBillNo("FB" + id);
        b.setPayableAmount(new BigDecimal(payable));
        b.setPaidAmount(new BigDecimal(paid));
        b.setWaivedAmount(BigDecimal.ZERO);
        b.setBillStatus(status);
        b.setContractId(2001L);
        b.setOrgId(7001L);
        b.setPersonId(4001L);
        b.setFeeItemId(1L);
        return b;
    }

    // ==================== 正常核销 ====================

    @Test
    @DisplayName("全额核销：账单 → PAID，剩余应付 0.00，收款单 → RECONCILED")
    void fullAllocate() {
        when(paymentMapper.selectById(1L)).thenReturn(payment(1L, "500", "0"));
        when(billMapper.selectById(2L)).thenReturn(bill(2L, "500", "0", "UNPAID"));

        BillVO vo = service.allocate(1L, 2L, new BigDecimal("500"));

        assertEquals("PAID", vo.billStatus());
        assertEquals("已缴", vo.billStatusLabel());
        assertEquals(0, BigDecimal.ZERO.compareTo(vo.payableAmount()),
                "剩余应付应为 0.00，实际 " + vo.payableAmount());
        assertEquals(0, new BigDecimal("500").compareTo(vo.paidAmount()));
    }

    @Test
    @DisplayName("部分核销：账单 → PARTIAL，收款单 → PARTIAL")
    void partialAllocate() {
        FinPayment p = payment(1L, "600", "0");
        FinBill b = bill(2L, "1000", "0", "UNPAID");
        when(paymentMapper.selectById(1L)).thenReturn(p);
        when(billMapper.selectById(2L)).thenReturn(b);

        BillVO vo = service.allocate(1L, 2L, new BigDecimal("400"));

        assertEquals("PARTIAL", vo.billStatus());
        assertEquals(0, new BigDecimal("600").compareTo(vo.payableAmount()));
        assertEquals(0, new BigDecimal("400").compareTo(vo.paidAmount()));
        // 收款单回写：已核销 400，部分核销
        assertEquals(0, new BigDecimal("400").compareTo(p.getReconciledAmount()));
        assertEquals("PARTIAL", p.getReconcileStatus());
    }

    @Test
    @DisplayName("不传核销金额 → 默认核销账单全部应付")
    void defaultAmountIsFullPayable() {
        when(paymentMapper.selectById(1L)).thenReturn(payment(1L, "1000", "0"));
        when(billMapper.selectById(2L)).thenReturn(bill(2L, "300", "0", "UNPAID"));

        BillVO vo = service.allocate(1L, 2L, null);
        assertEquals("PAID", vo.billStatus());
        assertEquals(0, new BigDecimal("300").compareTo(vo.paidAmount()));
    }

    @Test
    @DisplayName("每次核销写一条核销明细（可追溯）")
    void writesAllocateDetail() {
        when(paymentMapper.selectById(1L)).thenReturn(payment(1L, "500", "0"));
        when(billMapper.selectById(2L)).thenReturn(bill(2L, "500", "0", "UNPAID"));

        service.allocate(1L, 2L, new BigDecimal("200"));

        ArgumentCaptor<FinPaymentAllocate> cap =
                ArgumentCaptor.forClass(FinPaymentAllocate.class);
        verify(allocateMapper, times(1)).insert(cap.capture());
        FinPaymentAllocate a = cap.getValue();
        assertEquals(1L, a.getPaymentId());
        assertEquals(2L, a.getBillId());
        assertEquals("PAY", a.getAllocateType());
        assertEquals(0, new BigDecimal("200").compareTo(a.getAllocateAmount()));
    }

    // ==================== 三重上限 ====================

    @Test
    @DisplayName("⭐上限1：核销额超收款单余额 → 拒绝")
    void exceedPaymentRemain() {
        // 收款 600，已核 400 → 余额 200
        when(paymentMapper.selectById(1L)).thenReturn(payment(1L, "600", "400"));
        when(billMapper.selectById(2L)).thenReturn(bill(2L, "1000", "0", "UNPAID"));

        BizException ex = assertThrows(BizException.class,
                () -> service.allocate(1L, 2L, new BigDecimal("300")));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
        assertTrue(ex.getMessage().contains("余额"), ex.getMessage());
    }

    @Test
    @DisplayName("⭐上限2：核销额超账单应付 → 拒绝")
    void exceedBillPayable() {
        when(paymentMapper.selectById(1L)).thenReturn(payment(1L, "1000", "0"));
        when(billMapper.selectById(2L)).thenReturn(bill(2L, "300", "0", "UNPAID"));

        BizException ex = assertThrows(BizException.class,
                () -> service.allocate(1L, 2L, new BigDecimal("500")));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
        assertTrue(ex.getMessage().contains("应付"), ex.getMessage());
    }

    @Test
    @DisplayName("⭐上限3：已缴账单不可再核销")
    void paidBillCannotAllocate() {
        when(paymentMapper.selectById(1L)).thenReturn(payment(1L, "1000", "0"));
        when(billMapper.selectById(2L)).thenReturn(bill(2L, "0", "500", "PAID"));

        BizException ex = assertThrows(BizException.class,
                () -> service.allocate(1L, 2L, new BigDecimal("100")));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
        assertTrue(ex.getMessage().contains("已缴"), ex.getMessage());
    }

    @Test
    @DisplayName("已免除账单不可核销")
    void waivedBillCannotAllocate() {
        when(paymentMapper.selectById(1L)).thenReturn(payment(1L, "1000", "0"));
        when(billMapper.selectById(2L)).thenReturn(bill(2L, "0", "0", "WAIVED"));

        BizException ex = assertThrows(BizException.class,
                () -> service.allocate(1L, 2L, new BigDecimal("100")));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    @Test
    @DisplayName("未成功的收款单不可核销（PENDING/FAILED）")
    void unsuccessfulPaymentCannotAllocate() {
        FinPayment p = payment(1L, "500", "0");
        p.setPayStatus("PENDING");
        when(paymentMapper.selectById(1L)).thenReturn(p);
        when(billMapper.selectById(2L)).thenReturn(bill(2L, "500", "0", "UNPAID"));

        BizException ex = assertThrows(BizException.class,
                () -> service.allocate(1L, 2L, new BigDecimal("100")));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    @Test
    @DisplayName("核销金额为 0 或负数 → 拒绝")
    void nonPositiveAmount() {
        when(paymentMapper.selectById(1L)).thenReturn(payment(1L, "500", "0"));
        when(billMapper.selectById(2L)).thenReturn(bill(2L, "500", "0", "UNPAID"));
        assertThrows(BizException.class,
                () -> service.allocate(1L, 2L, BigDecimal.ZERO));
        assertThrows(BizException.class,
                () -> service.allocate(1L, 2L, new BigDecimal("-1")));
    }

    @Test
    @DisplayName("收款单不存在 → 404；账单不存在 → 404")
    void notFound() {
        when(paymentMapper.selectById(9L)).thenReturn(null);
        BizException e1 = assertThrows(BizException.class,
                () -> service.allocate(9L, 2L, BigDecimal.ONE));
        assertEquals(ErrorCode.NOT_FOUND, e1.errorCode());

        when(paymentMapper.selectById(1L)).thenReturn(payment(1L, "500", "0"));
        when(billMapper.selectById(9L)).thenReturn(null);
        BizException e2 = assertThrows(BizException.class,
                () -> service.allocate(1L, 9L, BigDecimal.ONE));
        assertEquals(ErrorCode.NOT_FOUND, e2.errorCode());
    }
}
