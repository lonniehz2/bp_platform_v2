package com.yundao.bp.grant;

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
import com.yundao.bp.grant.entity.GrantEntitlement;
import com.yundao.bp.grant.entity.GrantReconcileDiff;
import com.yundao.bp.grant.entity.GrantTaskDetail;
import com.yundao.bp.grant.mapper.GrantEntitlementMapper;
import com.yundao.bp.grant.mapper.GrantReconcileDiffMapper;
import com.yundao.bp.grant.mapper.GrantTaskDetailMapper;
import com.yundao.bp.grant.service.impl.GrantReconcileServiceImpl;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
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
 * 授权对账测试。
 *
 * <p><b>为什么必须测</b>：授权是异步下发的，网络抖动/设备离线下会出现
 * 「本地显示已授权、门锁上其实没有」（住户被拒之门外），
 * 或「本地已撤销、门锁上还在」（该失效的没失效，安全风险）。
 * 这两类问题只有在住户刷不开门时才会暴露，必须靠对账主动发现。
 */
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class ReconcileTest {

    @Mock
    private GrantReconcileDiffMapper diffMapper;
    @Mock
    private GrantEntitlementMapper entitlementMapper;
    @Mock
    private GrantTaskDetailMapper taskDetailMapper;

    private GrantReconcileServiceImpl service;
    private final List<GrantReconcileDiff> recorded = new ArrayList<>();

    @BeforeEach
    void setUp() {
        service = new GrantReconcileServiceImpl(diffMapper, entitlementMapper, taskDetailMapper,
                new SnowflakeIdGenerator(1, 1));
        TenantContext.set(TenantInfo.of("350600", 1001L));
        when(diffMapper.insert(any(GrantReconcileDiff.class))).thenAnswer(inv -> {
            recorded.add(inv.getArgument(0));
            return 1;
        });
        recorded.clear();
    }

    @AfterEach
    void tearDown() {
        TenantContext.clear();
    }

    private static GrantEntitlement ent(long id, String no, long spaceId, String status,
                                        LocalDateTime end) {
        GrantEntitlement e = new GrantEntitlement();
        e.setId(id);
        e.setGrantNo(no);
        e.setTenantId("350600");
        e.setPersonId(4001L);
        e.setSpaceId(spaceId);
        e.setHouseId(spaceId + 1);
        e.setGrantStatus(status);
        e.setValidStart(LocalDateTime.now().minusDays(10));
        e.setValidEnd(end);
        e.setIsDeleted(0);
        return e;
    }

    private static GrantTaskDetail detail(long spaceId, String lockId, String status) {
        GrantTaskDetail d = new GrantTaskDetail();
        d.setSpaceId(spaceId);
        d.setLockId(lockId);
        d.setDetailStatus(status);
        return d;
    }

    // ==================== 一致性 ====================

    @Test
    @DisplayName("⭐ 有效权益 + 已成功下发 → 一致，无差异")
    void consistent() {
        when(entitlementMapper.selectList(any()))
                .thenReturn(List.of(ent(1, "G1", 100, "EFFECTIVE", null)));
        when(taskDetailMapper.selectList(any()))
                .thenReturn(List.of(detail(100, "LOCK-A", "SUCCESS")));

        Map<String, Object> r = service.reconcile(null);
        assertEquals(true, r.get("consistent"), String.valueOf(r));
        assertEquals(0, r.get("diffRecorded"));
        assertTrue(recorded.isEmpty(), "一致时不应写差异");
        assertTrue(String.valueOf(r.get("conclusion")).contains("一致"));
    }

    // ==================== ⭐ LOCAL_MISSING ====================

    @Test
    @DisplayName("⭐⭐ 有效权益但锁上无下发记录 → LOCAL_MISSING（住户打不开门）")
    void localMissing() {
        when(entitlementMapper.selectList(any()))
                .thenReturn(List.of(ent(1, "G1", 100, "EFFECTIVE", null)));
        when(taskDetailMapper.selectList(any())).thenReturn(List.of());

        Map<String, Object> r = service.reconcile(null);
        assertEquals(1, r.get("localMissing"), String.valueOf(r));
        assertEquals(1, r.get("diffRecorded"));
        assertEquals(false, r.get("consistent"));
        assertEquals(1, recorded.size());
        assertEquals("LOCAL_MISSING", recorded.get(0).getDiffType());
        assertEquals("PENDING", recorded.get(0).getHandleStatus());
        assertEquals(4001L, recorded.get(0).getPersonId());
    }

    @Test
    @DisplayName("⭐ 下发失败（非 SUCCESS）等同未下发 → LOCAL_MISSING")
    void failedPushCountsAsMissing() {
        when(entitlementMapper.selectList(any()))
                .thenReturn(List.of(ent(1, "G1", 100, "EFFECTIVE", null)));
        when(taskDetailMapper.selectList(any()))
                .thenReturn(List.of(detail(100, "LOCK-A", "FAILED")));

        Map<String, Object> r = service.reconcile(null);
        assertEquals(1, r.get("localMissing"), String.valueOf(r));
    }

    @Test
    @DisplayName("⭐ 权益已过期 → 不算「应有」，不产生 LOCAL_MISSING")
    void expiredEntitlementNotExpected() {
        when(entitlementMapper.selectList(any()))
                .thenReturn(List.of(ent(1, "G1", 100, "EFFECTIVE",
                        LocalDateTime.now().minusDays(1))));
        when(taskDetailMapper.selectList(any())).thenReturn(List.of());

        Map<String, Object> r = service.reconcile(null);
        assertEquals(0, r.get("localMissing"), String.valueOf(r));
    }

    @Test
    @DisplayName("⭐ 权益未到生效日 → 不算「应有」")
    void notStartedNotExpected() {
        GrantEntitlement e = ent(1, "G1", 100, "EFFECTIVE", null);
        e.setValidStart(LocalDateTime.now().plusDays(5));
        when(entitlementMapper.selectList(any())).thenReturn(List.of(e));
        when(taskDetailMapper.selectList(any())).thenReturn(List.of());

        assertEquals(0, service.reconcile(null).get("localMissing"));
    }

    // ==================== ⭐ IOT_EXTRA ====================

    @Test
    @DisplayName("⭐⭐ 权益已撤销但锁上仍有授权 → IOT_EXTRA（安全风险）")
    void iotExtra() {
        when(entitlementMapper.selectList(any()))
                .thenReturn(List.of(ent(1, "G1", 100, "REVOKED", null)));
        when(taskDetailMapper.selectList(any()))
                .thenReturn(List.of(detail(100, "LOCK-A", "SUCCESS")));

        Map<String, Object> r = service.reconcile(null);
        assertEquals(1, r.get("iotExtra"), String.valueOf(r));
        assertEquals(1, recorded.size());
        assertEquals("IOT_EXTRA", recorded.get(0).getDiffType());
        assertEquals("LOCK-A", recorded.get(0).getLockId());
    }

    @Test
    @DisplayName("⭐ 同一空间多把锁 → 每条差异记一把锁")
    void multipleLocks() {
        when(entitlementMapper.selectList(any()))
                .thenReturn(List.of(ent(1, "G1", 100, "REVOKED", null)));
        when(taskDetailMapper.selectList(any())).thenReturn(List.of(
                detail(100, "LOCK-A", "SUCCESS"),
                detail(100, "LOCK-B", "SUCCESS")));

        Map<String, Object> r = service.reconcile(null);
        assertEquals(2, r.get("iotExtra"), String.valueOf(r));
        assertEquals(2, recorded.size());
    }

    // ==================== 处置 ====================

    private static GrantReconcileDiff pendingDiff(long id, String type) {
        GrantReconcileDiff d = new GrantReconcileDiff();
        d.setId(id);
        d.setDiffType(type);
        d.setHandleStatus("PENDING");
        return d;
    }

    @Test
    @DisplayName("⭐ 处置 LOCAL_MISSING → REGRANT 成功")
    void handleRegrant() {
        when(diffMapper.selectById(9L)).thenReturn(pendingDiff(9, "LOCAL_MISSING"));
        GrantReconcileDiff d = service.handle(9L, "REGRANT", "已重新下发");
        assertEquals("HANDLED", d.getHandleStatus());
        assertEquals("REGRANT", d.getHandleAction());
        assertTrue(d.getHandleTime() != null);
    }

    @Test
    @DisplayName("⭐ 处置 IOT_EXTRA → REVOKE 成功")
    void handleRevoke() {
        when(diffMapper.selectById(9L)).thenReturn(pendingDiff(9, "IOT_EXTRA"));
        assertEquals("HANDLED", service.handle(9L, "REVOKE", "已撤销").getHandleStatus());
    }

    @Test
    @DisplayName("⭐⭐ 动作与差异类型不匹配 → 拒绝（防误操作）")
    void actionTypeMismatch() {
        when(diffMapper.selectById(9L)).thenReturn(pendingDiff(9, "IOT_EXTRA"));
        BizException ex = assertThrows(BizException.class,
                () -> service.handle(9L, "REGRANT", "x"));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
        assertTrue(ex.getMessage().contains("重新授权"), ex.getMessage());
    }

    @Test
    @DisplayName("⭐ 重复处置 → 拒绝")
    void handleTwice() {
        GrantReconcileDiff d = pendingDiff(9, "LOCAL_MISSING");
        d.setHandleStatus("HANDLED");
        when(diffMapper.selectById(9L)).thenReturn(d);
        BizException ex = assertThrows(BizException.class,
                () -> service.handle(9L, "REGRANT", "x"));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    @Test
    @DisplayName("忽略处置 → IGNORED（不算已修复）")
    void handleIgnore() {
        when(diffMapper.selectById(9L)).thenReturn(pendingDiff(9, "LOCAL_MISSING"));
        assertEquals("IGNORED", service.handle(9L, "IGNORED", "已知问题").getHandleStatus());
    }

    @Test
    @DisplayName("非法处置动作 → 拒绝")
    void invalidAction() {
        when(diffMapper.selectById(9L)).thenReturn(pendingDiff(9, "LOCAL_MISSING"));
        assertThrows(BizException.class, () -> service.handle(9L, "DELETE", "x"));
    }

    @Test
    @DisplayName("差异不存在 → 404")
    void notFound() {
        when(diffMapper.selectById(9L)).thenReturn(null);
        assertEquals(ErrorCode.NOT_FOUND,
                assertThrows(BizException.class,
                        () -> service.handle(9L, "MANUAL", "x")).errorCode());
    }

    // ==================== 统计 ====================

    @Test
    @DisplayName("⭐⭐ 风险分级：IoT 多余 > 本地缺少 > 无差异")
    void riskLevel() {
        GrantReconcileDiff extra = pendingDiff(1, "IOT_EXTRA");
        GrantReconcileDiff missing = pendingDiff(2, "LOCAL_MISSING");
        when(diffMapper.selectList(any())).thenReturn(List.of(extra, missing));
        Map<String, Object> s = service.stats();
        assertEquals("HIGH", s.get("riskLevel"), String.valueOf(s));
        assertEquals(1, ((Map<?, ?>) s.get("byType")).get("IOT_EXTRA"));

        when(diffMapper.selectList(any())).thenReturn(List.of(missing));
        assertEquals("MEDIUM", service.stats().get("riskLevel"));

        when(diffMapper.selectList(any())).thenReturn(List.of());
        assertEquals("LOW", service.stats().get("riskLevel"));
    }
}
