# -*- coding: utf-8 -*-
"""生成资金核销测试 + 补贴计算测试"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\test\java\com\yundao\bp'

# ==================== 1) 核销三重上限 ====================
ALLOC_TEST = r'''package com.yundao.bp.fin;

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
'''

# ==================== 2) 补贴计算 ====================
SUBSIDY_TEST = r'''package com.yundao.bp.fin;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import com.yundao.bp.asset.entity.AssetHouse;
import com.yundao.bp.asset.mapper.AssetHouseMapper;
import com.yundao.bp.biz.entity.BizContract;
import com.yundao.bp.biz.entity.BizContractCohabitant;
import com.yundao.bp.biz.mapper.BizContractCohabitantMapper;
import com.yundao.bp.biz.mapper.BizContractMapper;
import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
import com.yundao.bp.fin.dto.SubsidyCalcCmd;
import com.yundao.bp.fin.entity.FinSubsidyStandard;
import com.yundao.bp.fin.mapper.FinBillMapper;
import com.yundao.bp.fin.mapper.FinSubsidyRecordMapper;
import com.yundao.bp.fin.mapper.FinSubsidyStandardMapper;
import com.yundao.bp.fin.service.SubsidyService;
import com.yundao.bp.fin.service.impl.SubsidyServiceImpl;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;
import org.springframework.test.util.ReflectionTestUtils;

/**
 * 补贴计算测试。
 *
 * <p>补贴直接决定财政支出与住户到手金额，算错即错发钱。
 * 覆盖 <b>4 种补贴方式 + 月度封顶 + 按人取同住人 + 缺数据报错</b>。
 */
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class SubsidyCalcTest {

    @Mock
    private FinSubsidyStandardMapper standardMapper;
    @Mock
    private FinSubsidyRecordMapper recordMapper;
    @Mock
    private FinBillMapper billMapper;
    @Mock
    private BizContractMapper contractMapper;
    @Mock
    private AssetHouseMapper houseMapper;
    @Mock
    private BizContractCohabitantMapper cohabitantMapper;

    private SubsidyServiceImpl service;

    private static FinSubsidyStandard std(String mode, String value, String cap) {
        FinSubsidyStandard s = new FinSubsidyStandard();
        s.setId(10L);
        s.setStandardCode("SUB-" + mode);
        s.setStandardName("测试标准");
        s.setSecurityType("PUBLIC");
        s.setSubsidyMode(mode);
        s.setSubsidyValue(new BigDecimal(value));
        s.setMaxAmount(cap == null ? null : new BigDecimal(cap));
        s.setStatus("ENABLED");
        s.setEffectiveStart(LocalDate.now().minusDays(1));
        return s;
    }

    private static BizContract contract() {
        BizContract c = new BizContract();
        c.setId(2001L);
        c.setContractNo("BC2001");
        c.setTenantId("350600");
        c.setOrgId(7001L);
        c.setHouseId(5001L);
        c.setLesseePersonId(4001L);
        c.setLesseeName("张三");
        c.setContractType("PUBLIC_RENTAL");
        c.setMonthlyRent(new BigDecimal("1000"));
        c.setContractStatus("EFFECTIVE");
        return c;
    }

    private void givenStandard(FinSubsidyStandard s) {
        when(contractMapper.selectById(2001L)).thenReturn(contract());
        when(standardMapper.selectList(any())).thenReturn(List.of(s));
        when(standardMapper.selectById(10L)).thenReturn(s);
    }

    @BeforeEach
    void setUp() {
        service = new SubsidyServiceImpl(standardMapper, recordMapper, billMapper,
                contractMapper, houseMapper, new SnowflakeIdGenerator(1, 1));
        TenantContext.set(TenantInfo.of("350600", 1001L));
        AssetHouse h = new AssetHouse();
        h.setId(5001L);
        h.setArea(new BigDecimal("80"));
        when(houseMapper.selectById(5001L)).thenReturn(h);
    }

    @AfterEach
    void tearDown() {
        TenantContext.clear();
    }

    private SubsidyService.SubsidyCalcResult preview(SubsidyCalcCmd cmd) {
        return service.preview(cmd);
    }

    // ==================== 4 种方式 ====================

    @Test
    @DisplayName("FIXED 定额：800 → 800.00")
    void fixed() {
        givenStandard(std("FIXED", "800", null));
        var r = preview(new SubsidyCalcCmd(2001L, null, null, null, null));
        assertEquals(0, new BigDecimal("800").compareTo(r.cappedAmount()));
        assertFalse(r.capped());
    }

    @Test
    @DisplayName("BY_AREA 按面积：20 × 80㎡ = 1600，封顶 1500 → 1500.00 且 capped=true")
    void byAreaWithCap() {
        givenStandard(std("BY_AREA", "20", "1500"));
        var r = preview(new SubsidyCalcCmd(2001L, null, null, null, null));
        assertEquals(0, new BigDecimal("1600").compareTo(r.amount()), "封顶前应为 1600");
        assertEquals(0, new BigDecimal("1500").compareTo(r.cappedAmount()), "封顶后应为 1500");
        assertTrue(r.capped());
        assertTrue(r.explain().contains("封顶"), r.explain());
    }

    @Test
    @DisplayName("BY_AREA：未达封顶时原样（20 × 50 = 1000）")
    void byAreaUnderCap() {
        givenStandard(std("BY_AREA", "20", "1500"));
        var r = preview(new SubsidyCalcCmd(2001L, null, new BigDecimal("50"), null, null));
        assertEquals(0, new BigDecimal("1000").compareTo(r.cappedAmount()));
        assertFalse(r.capped());
    }

    @Test
    @DisplayName("BY_PERSON 按人：300 × 3 人 = 900.00（显式传人数）")
    void byPersonExplicit() {
        givenStandard(std("BY_PERSON", "300", null));
        var r = preview(new SubsidyCalcCmd(2001L, null, null, 3, null));
        assertEquals(0, new BigDecimal("900").compareTo(r.cappedAmount()));
    }

    @Test
    @DisplayName("⭐BY_PERSON 未传人数 → 从同住人取（1 承租人 + 2 同住 = 3 人 → 900.00）")
    void byPersonFromCohabitants() {
        givenStandard(std("BY_PERSON", "300", null));
        ReflectionTestUtils.setField(service, "cohabitantMapper", cohabitantMapper);
        when(cohabitantMapper.selectCount(any())).thenReturn(2L);

        var r = preview(new SubsidyCalcCmd(2001L, null, null, null, null));
        assertEquals(0, new BigDecimal("900").compareTo(r.cappedAmount()),
                "保障人口应为 1+2=3，实际结果 " + r.cappedAmount());
        assertTrue(r.explain().contains("3 人"), r.explain());
    }

    @Test
    @DisplayName("⭐BY_PERSON 无同住人信息时兜底 1 人（不报错）")
    void byPersonFallbackOne() {
        givenStandard(std("BY_PERSON", "300", null));
        // cohabitantMapper 未注入（null）→ 兜底 1 人
        var r = preview(new SubsidyCalcCmd(2001L, null, null, null, null));
        assertEquals(0, new BigDecimal("300").compareTo(r.cappedAmount()));
    }

    @Test
    @DisplayName("RATIO 按租金比例：1000 × 0.6 = 600.00")
    void ratio() {
        givenStandard(std("RATIO", "0.6", null));
        var r = preview(new SubsidyCalcCmd(2001L, null, null, null, null));
        assertEquals(0, new BigDecimal("600").compareTo(r.cappedAmount()));
    }

    @Test
    @DisplayName("RATIO 可覆盖月租金参与计算（1200 × 0.6 = 720.00）")
    void ratioWithExplicitRent() {
        givenStandard(std("RATIO", "0.6", null));
        var r = preview(new SubsidyCalcCmd(2001L, null, null, null, new BigDecimal("1200")));
        assertEquals(0, new BigDecimal("720").compareTo(r.cappedAmount()));
    }

    // ==================== 缺数据 / 异常 ====================

    @Test
    @DisplayName("⭐BY_AREA 但房源无面积 → 明确报错（含合同号与房源ID）")
    void byAreaNoArea() {
        givenStandard(std("BY_AREA", "20", null));
        AssetHouse h = new AssetHouse();
        h.setId(5001L);
        h.setArea(null);
        when(houseMapper.selectById(5001L)).thenReturn(h);

        BizException ex = assertThrows(BizException.class,
                () -> preview(new SubsidyCalcCmd(2001L, null, null, null, null)));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
        assertTrue(ex.getMessage().contains("面积"), ex.getMessage());
        assertTrue(ex.getMessage().contains("5001"), ex.getMessage());
    }

    @Test
    @DisplayName("找不到匹配的补贴标准 → 明确报错")
    void noStandard() {
        when(contractMapper.selectById(2001L)).thenReturn(contract());
        when(standardMapper.selectList(any())).thenReturn(List.of());
        BizException ex = assertThrows(BizException.class,
                () -> preview(new SubsidyCalcCmd(2001L, null, null, null, null)));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    @Test
    @DisplayName("合同不存在 → 404")
    void contractNotFound() {
        when(contractMapper.selectById(2001L)).thenReturn(null);
        BizException ex = assertThrows(BizException.class,
                () -> preview(new SubsidyCalcCmd(2001L, null, null, null, null)));
        assertEquals(ErrorCode.NOT_FOUND, ex.errorCode());
    }

    @Test
    @DisplayName("结果 explain 含计算口径（审计与前端展示需要）")
    void explainPresent() {
        givenStandard(std("FIXED", "800", null));
        var r = preview(new SubsidyCalcCmd(2001L, null, null, null, null));
        assertTrue(r.explain().contains("定额"), r.explain());
        assertEquals("FIXED", r.subsidyMode());
        assertEquals("SUB-FIXED", r.standardCode());
    }
}
'''

for rel, src in (('fin/BillingAllocateTest.java', ALLOC_TEST),
                 ('fin/SubsidyCalcTest.java', SUBSIDY_TEST)):
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(src)
    print('  + %s（%d 行）' % (rel, src.count('\n')))
