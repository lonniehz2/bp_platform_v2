package com.yundao.bp.biz;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import com.yundao.bp.biz.constant.ContractStatus;
import com.yundao.bp.biz.dto.ContractCreateCmd;
import com.yundao.bp.biz.dto.ContractVO;
import com.yundao.bp.biz.entity.BizContract;
import com.yundao.bp.biz.mapper.BizContractMapper;
import com.yundao.bp.biz.service.ContractService;
import com.yundao.bp.biz.service.impl.ContractServiceImpl;
import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
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

/**
 * 合同测试。
 *
 * <p>核心验证：
 * <ol>
 *   <li><b>金额自动计算</b>：actualPay = 月租金 - 补贴，且不得为负</li>
 *   <li><b>租期自动计算</b>：起止日 → 整月数</li>
 *   <li><b>状态机</b>：不可跳步；纸质合同可从待签约直接生效</li>
 *   <li><b>续签/终止/到期扫描</b></li>
 * </ol>
 */
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class ContractModuleTest {

    @Mock
    private BizContractMapper mapper;

    private ContractService service;

    @BeforeEach
    void setUp() {
        service = new ContractServiceImpl(mapper, new SnowflakeIdGenerator(1, 1));
        TenantContext.set(TenantInfo.of("350600", 1001L));
        when(mapper.insert(any(BizContract.class))).thenReturn(1);
        when(mapper.updateById(any(BizContract.class))).thenReturn(1);
    }

    @AfterEach
    void tearDown() {
        TenantContext.clear();
    }

    private static ContractCreateCmd cmd(String monthlyRent, String subsidy) {
        return new ContractCreateCmd("PUBLIC_RENTAL", 7001L, 7100L, 4001L,
                "张三", "13800138000", "110105********002X",
                5001L, 6001L, "1幢1单元1层101室", new BigDecimal("89.50"),
                LocalDate.of(2026, 1, 1), LocalDate.of(2027, 1, 1),
                new BigDecimal("12.50"), "HOUSE_MONTH",
                new BigDecimal(monthlyRent), new BigDecimal("1000"),
                new BigDecimal(subsidy), "MONTH", 5, "ELECTRONIC",
                null, null, null, null, "保障房合同");
    }

    private static BizContract contract(String status, String signType) {
        BizContract e = new BizContract();
        e.setId(1L);
        e.setTenantId("350600");
        e.setContractNo("BC1");
        e.setContractType("PUBLIC_RENTAL");
        e.setContractStatus(status);
        e.setSignType(signType);
        e.setMonthlyRent(new BigDecimal("1000"));
        e.setSubsidyAmount(new BigDecimal("300"));
        e.setDepositAmount(new BigDecimal("1000"));
        e.setLeaseStart(LocalDate.now().minusMonths(6));
        e.setLeaseEnd(LocalDate.now().plusMonths(6));
        e.setLeaseMonths(12);
        e.setHouseId(5001L);
        e.setAutoGrant(1);
        e.setAutoExpire(1);
        return e;
    }

    // ==================== 1. 起草与金额计算 ====================

    @Test
    @DisplayName("起草合同：DRAFT + 单号 BC + 实付 = 月租金 - 补贴")
    void createContract() {
        ContractVO vo = service.create(cmd("1000", "300"));

        assertEquals("DRAFT", vo.contractStatus());
        assertEquals("草稿", vo.contractStatusLabel());
        assertTrue(vo.contractNo().startsWith("BC"));
        assertEquals(0, new BigDecimal("1000").compareTo(vo.monthlyRent()));
        assertEquals(0, new BigDecimal("300").compareTo(vo.subsidyAmount()));
        assertEquals(0, new BigDecimal("700").compareTo(vo.actualPay()),
                "实付应自动 = 1000 - 300");
        assertEquals(1, vo.autoGrant(), "默认开启自动授权");
        assertEquals(1, vo.autoExpire());
        assertFalse(vo.occupying(), "草稿不占房");
    }

    @Test
    @DisplayName("⭐ 租期自动计算：1 年 → 12 个月")
    void leaseMonthsComputed() {
        ContractVO vo = service.create(cmd("1000", "0"));
        assertEquals(12, vo.leaseMonths(), "365 天应算 12 个月");
    }

    @Test
    @DisplayName("⭐ 补贴超过月租金 → 拒绝（实付为负）")
    void subsidyCannotExceedRent() {
        BizException ex = assertThrows(BizException.class,
                () -> service.create(cmd("500", "800")));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
        assertTrue(ex.getMessage().contains("补贴"));
    }

    @Test
    @DisplayName("止租日必须晚于起租日")
    void leaseEndMustBeAfterStart() {
        ContractCreateCmd bad = new ContractCreateCmd("PUBLIC_RENTAL", 7001L, 7100L, 4001L,
                "张三", null, null, 5001L, 6001L, null, null,
                LocalDate.of(2027, 1, 1), LocalDate.of(2026, 1, 1),
                new BigDecimal("12.5"), "HOUSE_MONTH", new BigDecimal("1000"),
                null, null, "MONTH", 1, "ELECTRONIC", null, null, null, null, null);
        BizException ex = assertThrows(BizException.class, () -> service.create(bad));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
    }

    @Test
    @DisplayName("押金/补贴为空按 0 处理")
    void nullAmountsDefaultToZero() {
        ContractCreateCmd c = new ContractCreateCmd("LEASE", 7001L, 7100L, 4001L,
                null, null, null, 5001L, 6001L, null, null,
                LocalDate.of(2026, 1, 1), LocalDate.of(2026, 7, 1),
                new BigDecimal("10"), "AREA_MONTH", new BigDecimal("800"),
                null, null, "QUARTER", 1, "PAPER", null, null, null, null, null);
        ContractVO vo = service.create(c);
        assertEquals(0, BigDecimal.ZERO.compareTo(vo.depositAmount()));
        assertEquals(0, BigDecimal.ZERO.compareTo(vo.subsidyAmount()));
        assertEquals(0, new BigDecimal("800").compareTo(vo.actualPay()));
    }

    @Test
    @DisplayName("无租户上下文拒绝")
    void noTenant() {
        TenantContext.clear();
        BizException ex = assertThrows(BizException.class,
                () -> service.create(cmd("1000", "0")));
        assertEquals(ErrorCode.TENANT_CONTEXT_MISSING, ex.errorCode());
    }

    // ==================== 2. 状态机 ====================

    @Test
    @DisplayName("完整生命周期：DRAFT → 待签约 → 签约中 → 履约中")
    void fullLifecycle() {
        BizContract e = contract("DRAFT", "ELECTRONIC");
        when(mapper.selectById(1L)).thenReturn(e);

        assertEquals("PENDING_SIGN", service.submitSign(1L).contractStatus());
        assertEquals("SIGNING", service.startSigning(1L, "QYS").contractStatus());
        ContractVO vo = service.sign(1L, "https://x/c.pdf", "FLOW-1");
        assertEquals("EFFECTIVE", vo.contractStatus());
        assertEquals("履约中", vo.contractStatusLabel());
        assertTrue(vo.occupying(), "履约中应占房");
        assertNotNull(e.getSignTime());
        assertNotNull(e.getEffectiveTime());
        assertEquals("QYS", e.getSignVendor());
        assertEquals("https://x/c.pdf", e.getSignFileUrl());
    }

    @Test
    @DisplayName("⭐ 状态机不可跳步：DRAFT 直接生效被拒")
    void cannotSkipSteps() {
        BizContract e = contract("DRAFT", "ELECTRONIC");
        when(mapper.selectById(1L)).thenReturn(e);
        BizException ex = assertThrows(BizException.class,
                () -> service.sign(1L, null, null));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    @Test
    @DisplayName("⭐ 纸质合同可从待签约直接生效")
    void paperContractCanSignFromPending() {
        BizContract e = contract("PENDING_SIGN", "PAPER");
        when(mapper.selectById(1L)).thenReturn(e);
        ContractVO vo = service.sign(1L, "file://paper.pdf", null);
        assertEquals("EFFECTIVE", vo.contractStatus());
    }

    @Test
    @DisplayName("已终止合同不可再流转")
    void terminalCannotMove() {
        BizContract e = contract("TERMINATED", "ELECTRONIC");
        when(mapper.selectById(1L)).thenReturn(e);
        assertThrows(BizException.class, () -> service.submitSign(1L));
        assertThrows(BizException.class, () -> service.terminate(1L, "x"));
    }

    @Test
    @DisplayName("合同不存在报 404")
    void notFound() {
        when(mapper.selectById(any())).thenReturn(null);
        BizException ex = assertThrows(BizException.class, () -> service.get(999L));
        assertEquals(ErrorCode.NOT_FOUND, ex.errorCode());
    }

    // ==================== 3. 续签 ====================

    @Test
    @DisplayName("⭐ 续签：止租日顺延 + 金额重算 + 状态 RENEWING")
    void renewContract() {
        BizContract e = contract("EFFECTIVE", "ELECTRONIC");
        LocalDate oldEnd = e.getLeaseEnd();
        LocalDate newEnd = oldEnd.plusYears(1);
        when(mapper.selectById(1L)).thenReturn(e);

        ContractVO vo = service.renew(1L, newEnd, new BigDecimal("1200"));
        assertEquals("RENEWING", vo.contractStatus());
        assertEquals(oldEnd, vo.leaseStart(), "新起租日 = 原止租日");
        assertEquals(newEnd, vo.leaseEnd());
        assertEquals(0, new BigDecimal("1200").compareTo(vo.monthlyRent()));
        assertEquals(0, new BigDecimal("900").compareTo(vo.actualPay()), "1200 - 300 = 900");
        assertTrue(vo.occupying(), "续签中仍占房");
    }

    @Test
    @DisplayName("续签止租日必须晚于原止租日")
    void renewRequiresLaterEnd() {
        BizContract e = contract("EFFECTIVE", "ELECTRONIC");
        when(mapper.selectById(1L)).thenReturn(e);
        BizException ex = assertThrows(BizException.class,
                () -> service.renew(1L, e.getLeaseEnd().minusDays(1), null));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
    }

    // ==================== 4. 终止与作废 ====================

    @Test
    @DisplayName("终止：履约中 → 已终止 + 记录原因/时间")
    void terminateContract() {
        BizContract e = contract("EFFECTIVE", "ELECTRONIC");
        when(mapper.selectById(1L)).thenReturn(e);

        ContractVO vo = service.terminate(1L, "承租人退租");
        assertEquals("TERMINATED", vo.contractStatus());
        assertEquals("已终止", vo.contractStatusLabel());
        assertEquals("承租人退租", vo.terminateReason());
        assertNotNull(vo.terminateTime());
    }

    @Test
    @DisplayName("作废：草稿可作废")
    void cancelDraft() {
        BizContract e = contract("DRAFT", "ELECTRONIC");
        when(mapper.selectById(1L)).thenReturn(e);
        assertEquals("CANCELLED", service.cancel(1L, "信息有误").contractStatus());
    }

    @Test
    @DisplayName("⭐ 履约中不可作废（只能终止）")
    void cannotCancelEffective() {
        BizContract e = contract("EFFECTIVE", "ELECTRONIC");
        when(mapper.selectById(1L)).thenReturn(e);
        assertThrows(BizException.class, () -> service.cancel(1L, "x"));
    }

    // ==================== 5. 到期扫描与派生指标 ====================

    @Test
    @DisplayName("⭐ 到期扫描：已过止租日的履约中合同置为 EXPIRED")
    void expireDue() {
        BizContract expired = contract("EFFECTIVE", "ELECTRONIC");
        expired.setLeaseEnd(LocalDate.now().minusDays(1));
        BizContract alive = contract("EFFECTIVE", "ELECTRONIC");
        alive.setId(2L);
        alive.setLeaseEnd(LocalDate.now().plusDays(30));
        when(mapper.selectList(any())).thenReturn(List.of(expired));

        int n = service.expireDue();
        assertEquals(1, n);
        assertEquals("EXPIRED", expired.getContractStatus());
    }

    @Test
    @DisplayName("⭐ 即将到期：30 天内 → expiringSoon=true")
    void expiringSoonDerived() {
        BizContract e = contract("EFFECTIVE", "ELECTRONIC");
        e.setLeaseEnd(LocalDate.now().plusDays(10));
        when(mapper.selectById(1L)).thenReturn(e);

        ContractVO vo = service.get(1L);
        assertTrue(vo.expiringSoon());
        assertEquals(10L, vo.daysToExpire());
    }

    @Test
    @DisplayName("远期合同不判即将到期")
    void notExpiringSoon() {
        BizContract e = contract("EFFECTIVE", "ELECTRONIC");
        e.setLeaseEnd(LocalDate.now().plusDays(300));
        when(mapper.selectById(1L)).thenReturn(e);
        assertFalse(service.get(1L).expiringSoon());
    }

    @Test
    @DisplayName("非履约状态不计算剩余天数")
    void noDaysToExpireWhenDraft() {
        BizContract e = contract("DRAFT", "ELECTRONIC");
        when(mapper.selectById(1L)).thenReturn(e);
        ContractVO vo = service.get(1L);
        assertNull(vo.daysToExpire());
        assertFalse(vo.expiringSoon());
    }

    // ==================== 6. 状态机定义 ====================

    @Test
    @DisplayName("合同状态机定义")
    void statusMachine() {
        assertTrue(ContractStatus.nextOf(ContractStatus.DRAFT)
                .contains(ContractStatus.PENDING_SIGN));
        assertFalse(ContractStatus.nextOf(ContractStatus.DRAFT)
                .contains(ContractStatus.EFFECTIVE), "DRAFT 不可直达 EFFECTIVE");
        assertTrue(ContractStatus.nextOf(ContractStatus.EFFECTIVE)
                .contains(ContractStatus.TERMINATED));
        assertTrue(ContractStatus.nextOf(ContractStatus.TERMINATED).isEmpty());
        assertTrue(ContractStatus.EFFECTIVE.isOccupying());
        assertTrue(ContractStatus.RENEWING.isOccupying());
        assertFalse(ContractStatus.EXPIRED.isOccupying());
        assertFalse(ContractStatus.EFFECTIVE.isTerminal());
    }
}
