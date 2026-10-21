package com.yundao.bp.biz;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import com.yundao.bp.biz.constant.SettleStatus;
import com.yundao.bp.biz.constant.TerminationStatus;
import com.yundao.bp.biz.dto.TerminationCreateCmd;
import com.yundao.bp.biz.dto.TerminationVO;
import com.yundao.bp.biz.entity.BizTermination;
import com.yundao.bp.biz.mapper.BizTerminationMapper;
import com.yundao.bp.biz.service.TerminationService;
import com.yundao.bp.biz.service.impl.TerminationServiceImpl;
import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
import java.math.BigDecimal;
import java.time.LocalDate;
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
 * 退租腾退测试。
 *
 * <p>核心验证：
 * <ol>
 *   <li><b>政策口径</b>：重庆过渡期 3 个月/1.5 倍；成都搬迁期上限 6 个月；违规清退 5 年禁申</li>
 *   <li><b>结算公式</b>：押金退还 - 欠费 - 损坏赔偿（正退负补）</li>
 *   <li><b>办结四前置</b>：验房通过 + 结算完成 + 房源释放 + 授权回收</li>
 * </ol>
 */
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class TerminationModuleTest {

    @Mock
    private BizTerminationMapper mapper;

    private TerminationService service;

    @BeforeEach
    void setUp() {
        service = new TerminationServiceImpl(mapper, new SnowflakeIdGenerator(1, 1));
        TenantContext.set(TenantInfo.of("350600", 1001L));
        when(mapper.insert(any(BizTermination.class))).thenReturn(1);
        when(mapper.updateById(any(BizTermination.class))).thenReturn(1);
    }

    @AfterEach
    void tearDown() {
        TenantContext.clear();
    }

    private static TerminationCreateCmd cmd(String type, Integer relocMonths) {
        return new TerminationCreateCmd(2001L, 5001L, 4001L, type,
                LocalDate.now().plusDays(30), "承租人工作调动", null, null, relocMonths);
    }

    private static BizTermination tm(String status) {
        BizTermination e = new BizTermination();
        e.setId(1L);
        e.setTenantId("350600");
        e.setTerminationNo("BT1");
        e.setContractId(2001L);
        e.setHouseId(5001L);
        e.setPersonId(4001L);
        e.setTerminationType("NORMAL");
        e.setTerminationStatus(status);
        e.setInspectStatus("PENDING");
        e.setSettleStatus("PENDING");
        e.setDamageAmount(BigDecimal.ZERO);
        e.setHouseReleased(0);
        e.setGrantRevoked(0);
        e.setEnforceFlag(0);
        e.setNotaryFlag(0);
        return e;
    }

    // ==================== 1. 申请与政策参数 ====================

    @Test
    @DisplayName("申请退租：APPLYING + 单号 BT + 重庆过渡期 3 个月/1.5 倍")
    void applyNormal() {
        TerminationVO vo = service.apply(cmd("NORMAL", null));

        assertEquals("APPLYING", vo.terminationStatus());
        assertEquals("申请中", vo.terminationStatusLabel());
        assertTrue(vo.terminationNo().startsWith("BT"));
        assertEquals(3, vo.transitionMonths(), "重庆腾退过渡期默认 3 个月");
        assertEquals(0, new BigDecimal("1.5").compareTo(vo.transitionRentMultiplier()));
        assertNotNull(vo.transitionStartDate());
        assertNotNull(vo.transitionEndDate());
        assertEquals("PENDING", vo.inspectStatus());
        assertEquals("PENDING", vo.settleStatus());
        assertFalse(vo.houseReleased(), "初始未释放房源");
        assertFalse(vo.grantRevoked());
        assertFalse(vo.readyToComplete(), "前置未齐不可办结");
    }

    @Test
    @DisplayName("⭐ 违规清退：登记 5 年禁申 + 给过渡期")
    void applyExpel() {
        TerminationVO vo = service.apply(cmd("EXPEL", null));
        assertEquals("EXPEL", vo.terminationType());
        assertNotNull(vo.banReapplyEndDate(), "违规清退应登记限制再申请结束日");
        assertEquals(LocalDate.now().plusYears(5), vo.banReapplyEndDate());
        assertEquals(3, vo.transitionMonths());
    }

    @Test
    @DisplayName("⭐ 成都搬迁期：可选，最长 6 个月")
    void relocation() {
        TerminationVO vo = service.apply(cmd("EXCHANGE", 6));
        assertNotNull(vo.relocationStartDate());
        assertNotNull(vo.relocationEndDate());
        assertEquals(vo.planExitDate().plusMonths(6), vo.relocationEndDate());
    }

    @Test
    @DisplayName("⭐ 搬迁期超过 6 个月被拒（成都政策）")
    void relocationMaxSixMonths() {
        BizException ex = assertThrows(BizException.class,
                () -> service.apply(cmd("NORMAL", 7)));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
        assertTrue(ex.getMessage().contains("6"), ex.getMessage());
    }

    @Test
    @DisplayName("无租户上下文拒绝")
    void noTenant() {
        TenantContext.clear();
        BizException ex = assertThrows(BizException.class, () -> service.apply(cmd("NORMAL", null)));
        assertEquals(ErrorCode.TENANT_CONTEXT_MISSING, ex.errorCode());
    }

    // ==================== 2. 审批状态机 ====================

    @Test
    @DisplayName("审批流转：APPLYING → APPROVING → APPROVED")
    void approvalFlow() {
        BizTermination e = tm("APPLYING");
        when(mapper.selectById(1L)).thenReturn(e);

        assertEquals("APPROVING", service.submit(1L).terminationStatus());
        assertEquals("APPROVED", service.approve(1L, "同意退租").terminationStatus());
        assertEquals("已批准", service.get(1L).terminationStatusLabel());
    }

    @Test
    @DisplayName("⭐ 状态机不可跳步：APPLYING 直接批准被拒")
    void cannotSkipApproval() {
        BizTermination e = tm("APPLYING");
        when(mapper.selectById(1L)).thenReturn(e);
        BizException ex = assertThrows(BizException.class, () -> service.approve(1L, "x"));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    @Test
    @DisplayName("驳回 → REJECTED（终态）")
    void reject() {
        BizTermination e = tm("APPROVING");
        when(mapper.selectById(1L)).thenReturn(e);
        assertEquals("REJECTED", service.reject(1L, "材料不全").terminationStatus());
        assertThrows(BizException.class, () -> service.approve(1L, "x"));
    }

    @Test
    @DisplayName("撤单：APPLYING → CANCELLED")
    void cancel() {
        BizTermination e = tm("APPLYING");
        when(mapper.selectById(1L)).thenReturn(e);
        assertEquals("CANCELLED", service.cancel(1L, "继续租住").terminationStatus());
    }

    // ==================== 3. 验房与结算 ====================

    @Test
    @DisplayName("验房：记录结果与损坏赔偿")
    void inspect() {
        BizTermination e = tm("APPROVED");
        when(mapper.selectById(1L)).thenReturn(e);

        TerminationVO vo = service.inspect(1L, "ABNORMAL", "墙面有破损",
                new BigDecimal("300"), "img1.jpg,img2.jpg");
        assertEquals("ABNORMAL", vo.inspectStatus());
        assertEquals(0, new BigDecimal("300").compareTo(vo.damageAmount()));
        assertEquals("墙面有破损", vo.inspectResult());
    }

    @Test
    @DisplayName("验房赔偿为负被拒")
    void negativeDamageRejected() {
        BizTermination e = tm("APPROVED");
        when(mapper.selectById(1L)).thenReturn(e);
        assertThrows(BizException.class, () -> service.inspect(1L, "PASSED", "ok",
                new BigDecimal("-1"), null));
    }

    @Test
    @DisplayName("⭐ 结算公式：押金退还 - 欠费 - 损坏赔偿")
    void settleFormula() {
        BizTermination e = tm("APPROVED");
        e.setDamageAmount(new BigDecimal("300"));
        when(mapper.selectById(1L)).thenReturn(e);

        TerminationVO vo = service.settle(1L, new BigDecimal("2000"), new BigDecimal("500"));
        // 2000 - 500 - 300 = 1200
        assertEquals(0, new BigDecimal("1200").compareTo(vo.settleAmount()));
        assertEquals("SETTLED", vo.settleStatus());
        assertEquals("已结算", vo.settleStatusLabel());
    }

    @Test
    @DisplayName("欠费+损坏超过押金 → 结算金额为负（需补缴）")
    void settleNegative() {
        BizTermination e = tm("APPROVED");
        e.setDamageAmount(new BigDecimal("500"));
        when(mapper.selectById(1L)).thenReturn(e);

        TerminationVO vo = service.settle(1L, new BigDecimal("1000"), new BigDecimal("800"));
        // 1000 - 800 - 500 = -300
        assertEquals(0, new BigDecimal("-300").compareTo(vo.settleAmount()));
    }

    @Test
    @DisplayName("未批准不可结算")
    void cannotSettleBeforeApprove() {
        BizTermination e = tm("APPLYING");
        when(mapper.selectById(1L)).thenReturn(e);
        BizException ex = assertThrows(BizException.class,
                () -> service.settle(1L, BigDecimal.TEN, BigDecimal.ZERO));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    // ==================== 4. 办结四前置 ====================

    @Test
    @DisplayName("⭐ 前置不全不可办结：验房未通过")
    void cannotCompleteWithoutInspect() {
        BizTermination e = tm("APPROVED");
        when(mapper.selectById(1L)).thenReturn(e);
        BizException ex = assertThrows(BizException.class, () -> service.complete(1L, null));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
        assertTrue(ex.getMessage().contains("验房"));
    }

    @Test
    @DisplayName("⭐ 前置不全不可办结：结算未完成")
    void cannotCompleteWithoutSettle() {
        BizTermination e = tm("APPROVED");
        e.setInspectStatus("PASSED");
        when(mapper.selectById(1L)).thenReturn(e);
        BizException ex = assertThrows(BizException.class, () -> service.complete(1L, null));
        assertTrue(ex.getMessage().contains("结算"), ex.getMessage());
    }

    @Test
    @DisplayName("⭐ 前置不全不可办结：房源未释放")
    void cannotCompleteWithoutRelease() {
        BizTermination e = tm("APPROVED");
        e.setInspectStatus("PASSED");
        e.setSettleStatus("SETTLED");
        when(mapper.selectById(1L)).thenReturn(e);
        BizException ex = assertThrows(BizException.class, () -> service.complete(1L, null));
        assertTrue(ex.getMessage().contains("房源"), ex.getMessage());
    }

    @Test
    @DisplayName("⭐ 前置不全不可办结：授权未回收")
    void cannotCompleteWithoutRevoke() {
        BizTermination e = tm("APPROVED");
        e.setInspectStatus("PASSED");
        e.setSettleStatus("SETTLED");
        e.setHouseReleased(1);
        when(mapper.selectById(1L)).thenReturn(e);
        BizException ex = assertThrows(BizException.class, () -> service.complete(1L, null));
        assertTrue(ex.getMessage().contains("授权"), ex.getMessage());
    }

    @Test
    @DisplayName("⭐ 四前置齐备才可办结 → COMPLETED")
    void completeAllReady() {
        BizTermination e = tm("APPROVED");
        e.setInspectStatus("PASSED");
        e.setSettleStatus("SETTLED");
        e.setHouseReleased(1);
        e.setGrantRevoked(1);
        when(mapper.selectById(1L)).thenReturn(e);

        assertTrue(service.get(1L).readyToComplete(), "派生指标应判定可办结");
        TerminationVO vo = service.complete(1L, LocalDate.now());
        assertEquals("COMPLETED", vo.terminationStatus());
        assertEquals("已完成", vo.terminationStatusLabel());
        assertNotNull(vo.actualExitDate());
    }

    @Test
    @DisplayName("标记释放/回收后可再次推进")
    void markReleased() {
        BizTermination e = tm("APPROVED");
        when(mapper.selectById(1L)).thenReturn(e);
        TerminationVO vo = service.markReleased(1L, true, true);
        assertTrue(vo.houseReleased());
        assertTrue(vo.grantRevoked());
    }

    // ==================== 5. 强制执行与逾期 ====================

    @Test
    @DisplayName("登记强制执行 + 公证 + 物品处置人（成都要求）")
    void registerEnforce() {
        BizTermination e = tm("APPROVED");
        when(mapper.selectById(1L)).thenReturn(e);

        TerminationVO vo = service.registerEnforce(1L, LocalDate.now(), "芗城区人民法院",
                "李四", "13700137000", "公证字2026-001");
        assertTrue(vo.enforceFlag());
        assertEquals("芗城区人民法院", vo.enforceCourt());
        assertEquals("李四", vo.itemHandlerName());
        assertTrue(vo.notaryFlag());
        assertEquals("公证字2026-001", vo.notaryNo());
    }

    @Test
    @DisplayName("⭐ 逾期未退房：计划退房日已过但仍无实际退房日")
    void overdueExit() {
        BizTermination e = tm("APPROVED");
        e.setPlanExitDate(LocalDate.now().minusDays(5));
        when(mapper.selectById(1L)).thenReturn(e);
        assertTrue(service.get(1L).overdueExit());
    }

    @Test
    @DisplayName("已办结不判逾期")
    void completedNotOverdue() {
        BizTermination e = tm("COMPLETED");
        e.setPlanExitDate(LocalDate.now().minusDays(30));
        e.setActualExitDate(LocalDate.now().minusDays(28));
        when(mapper.selectById(1L)).thenReturn(e);
        assertFalse(service.get(1L).overdueExit());
    }

    @Test
    @DisplayName("退租单不存在报 404")
    void notFound() {
        when(mapper.selectById(any())).thenReturn(null);
        BizException ex = assertThrows(BizException.class, () -> service.get(999L));
        assertEquals(ErrorCode.NOT_FOUND, ex.errorCode());
    }

    // ==================== 6. 状态机定义 ====================

    @Test
    @DisplayName("退租状态机定义")
    void statusMachine() {
        assertTrue(TerminationStatus.nextOf(TerminationStatus.APPLYING)
                .contains(TerminationStatus.APPROVING));
        assertFalse(TerminationStatus.nextOf(TerminationStatus.APPLYING)
                .contains(TerminationStatus.APPROVED), "APPLYING 不可直达 APPROVED");
        assertTrue(TerminationStatus.nextOf(TerminationStatus.APPROVED)
                .contains(TerminationStatus.COMPLETED));
        assertTrue(TerminationStatus.nextOf(TerminationStatus.COMPLETED).isEmpty());
        assertTrue(TerminationStatus.COMPLETED.isTerminal());
        assertFalse(TerminationStatus.APPROVED.isTerminal());
    }

    @Test
    @DisplayName("结算状态枚举")
    void settleStatusEnum() {
        assertEquals("待结算", SettleStatus.PENDING.label());
        assertEquals("已结算", SettleStatus.SETTLED.label());
        assertEquals("已免除", SettleStatus.WAIVED.label());
    }
}
