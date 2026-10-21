package com.yundao.bp.grant;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
import com.yundao.bp.grant.constant.GrantStatus;
import com.yundao.bp.grant.constant.GrantTaskStatus;
import com.yundao.bp.grant.dto.GrantApplyCmd;
import com.yundao.bp.grant.dto.GrantVO;
import com.yundao.bp.grant.entity.GrantEntitlement;
import com.yundao.bp.grant.entity.GrantTask;
import com.yundao.bp.grant.entity.GrantTaskDetail;
import com.yundao.bp.grant.iot.IotGrantClient;
import com.yundao.bp.grant.iot.IotGrantRequest;
import com.yundao.bp.grant.iot.IotGrantResult;
import com.yundao.bp.grant.mapper.GrantEntitlementMapper;
import com.yundao.bp.grant.mapper.GrantTaskDetailMapper;
import com.yundao.bp.grant.mapper.GrantTaskMapper;
import com.yundao.bp.grant.mq.GrantDispatchProducer;
import com.yundao.bp.dev.service.DeviceBindingResolver;
import com.yundao.bp.grant.service.impl.GrantServiceImpl;
import java.time.LocalDateTime;
import java.util.List;
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
 * 授权编排测试。
 *
 * <p>覆盖编排的四个关键点：
 * <ol>
 *   <li><b>幂等</b>：同参数重复申请不重复建任务、不重复下发</li>
 *   <li><b>异步</b>：apply 只投递 MQ，不下发；dispatch 才下发</li>
 *   <li><b>状态机</b>：PENDING → DISPATCHING → SUCCESS/PARTIAL/FAILED</li>
 *   <li><b>降级</b>：IoT 失败可重试，超限转 FAILED</li>
 * </ol>
 */
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class GrantModuleTest {

    @Mock
    private GrantEntitlementMapper entitlementMapper;
    @Mock
    private GrantTaskMapper taskMapper;
    @Mock
    private GrantTaskDetailMapper detailMapper;
    @Mock
    private GrantDispatchProducer producer;
    @Mock
    private IotGrantClient iotClient;
    @Mock
    private DeviceBindingResolver deviceResolver;

    private GrantServiceImpl grantService;

    @BeforeEach
    void setUp() {
        grantService = new GrantServiceImpl(entitlementMapper, taskMapper, detailMapper,
                new SnowflakeIdGenerator(1, 1), producer, iotClient, deviceResolver);
        TenantContext.set(TenantInfo.of("350600", 1001L));
        when(entitlementMapper.insert(any(GrantEntitlement.class))).thenReturn(1);
        when(entitlementMapper.updateById(any(GrantEntitlement.class))).thenReturn(1);
        when(taskMapper.insert(any(GrantTask.class))).thenReturn(1);
        when(taskMapper.updateById(any(GrantTask.class))).thenReturn(1);
        when(detailMapper.insert(any(GrantTaskDetail.class))).thenReturn(1);
        when(deviceResolver.resolveDeviceIds(anyLong())).thenReturn(List.of("DEV-1"));
        // dispatch 会查权益拿空间锚点：必须给出有 spaceId 的权益
        GrantEntitlement entForDispatch = new GrantEntitlement();
        entForDispatch.setId(100L);
        entForDispatch.setTenantId("350600");
        entForDispatch.setSpaceId(6001L);
        entForDispatch.setGrantStatus("EFFECTIVE");
        when(entitlementMapper.selectById(100L)).thenReturn(entForDispatch);
    }

    @AfterEach
    void tearDown() {
        TenantContext.clear();
    }

    private static GrantApplyCmd cmd(String level, LocalDateTime end) {
        return new GrantApplyCmd(5001L, 6001L, level, null, end, null, "CONTRACT", 7001L, "测试授权");
    }

    // ==================== 1. 申请与异步 ====================

    @Test
    @DisplayName("申请授权：建权益(EFFECTIVE) + 建任务(PENDING) + 只投递不下发")
    void applyCreatesEntitlementAndTask() {
        when(taskMapper.selectOne(any())).thenReturn(null);

        GrantVO vo = grantService.apply(cmd("USAGE", LocalDateTime.now().plusDays(365)));

        assertEquals("EFFECTIVE", vo.grantStatus());
        assertEquals("已生效", vo.grantStatusLabel());
        assertEquals(5001L, vo.personId());
        assertEquals(6001L, vo.spaceId());
        assertEquals("USAGE", vo.grantLevel());
        assertTrue(vo.allowOpen(), "USAGE 应含开门权限");
        assertNotNull(vo.grantNo());

        // 任务必须落库且为 PENDING
        ArgumentCaptor<GrantTask> tc = ArgumentCaptor.forClass(GrantTask.class);
        verify(taskMapper).insert(tc.capture());
        assertEquals("PENDING", tc.getValue().getTaskStatus());
        assertEquals("GRANT", tc.getValue().getTaskType());
        assertEquals(0, tc.getValue().getRetryCount());

        // 只投递 MQ，绝不同步下发
        verify(producer, times(1)).publishDispatch(tc.getValue().getId());
        verify(iotClient, never()).grant(any());
    }

    @Test
    @DisplayName("OWNERSHIP 不含开门权限、可转授、允许无失效时间")
    void ownershipRules() {
        when(taskMapper.selectOne(any())).thenReturn(null);
        GrantVO vo = grantService.apply(cmd("OWNERSHIP", null));
        assertFalse(vo.allowOpen(), "所有权不含开门权限（DDL 注释）");
        assertNull(vo.validEnd(), "所有权允许永久");
    }

    @Test
    @DisplayName("非 OWNERSHIP 必须设失效时间")
    void nonOwnershipRequiresEnd() {
        BizException ex = assertThrows(BizException.class,
                () -> grantService.apply(cmd("USAGE", null)));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
        assertTrue(ex.getMessage().contains("OWNERSHIP"));
    }

    @Test
    @DisplayName("失效时间早于生效时间应被拒")
    void invalidValidityRange() {
        LocalDateTime start = LocalDateTime.now().plusDays(10);
        LocalDateTime end = LocalDateTime.now().plusDays(5);
        GrantApplyCmd c = new GrantApplyCmd(5001L, 6001L, "USAGE", start, end, null,
                "CONTRACT", 7001L, null);
        BizException ex = assertThrows(BizException.class, () -> grantService.apply(c));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
    }

    // ==================== 2. 幂等 ====================

    @Test
    @DisplayName("⭐ 幂等：同参数重复申请返回已有权益，不重复建任务")
    void idempotentApply() {
        GrantApplyCmd c = cmd("USAGE", LocalDateTime.now().plusDays(30));

        // 第一次：无已有任务
        when(taskMapper.selectOne(any())).thenReturn(null);
        grantService.apply(c);
        verify(taskMapper, times(1)).insert(any(GrantTask.class));

        // 第二次：模拟已存在 PENDING 任务
        GrantTask exist = new GrantTask();
        exist.setId(888L);
        exist.setEntitlementId(999L);
        exist.setTaskStatus("PENDING");
        when(taskMapper.selectOne(any())).thenReturn(exist);
        GrantEntitlement ent = new GrantEntitlement();
        ent.setId(999L);
        ent.setGrantStatus("EFFECTIVE");
        when(entitlementMapper.selectById(999L)).thenReturn(ent);

        grantService.apply(c);
        // 任务没有再次插入（仍为 1 次）
        verify(taskMapper, times(1)).insert(any(GrantTask.class));
    }

    @Test
    @DisplayName("幂等键对参数敏感：不同空间 → 不同键")
    void idempotentKeyDiffers() {
        LocalDateTime t = LocalDateTime.now();
        String k1 = GrantServiceImpl.idempotentKey(1L, 10L, "USAGE", t, t.plusDays(1));
        String k2 = GrantServiceImpl.idempotentKey(1L, 11L, "USAGE", t, t.plusDays(1));
        String k3 = GrantServiceImpl.idempotentKey(1L, 10L, "MANAGEMENT", t, t.plusDays(1));
        assertFalse(k1.equals(k2), "不同空间应不同");
        assertFalse(k1.equals(k3), "不同层级应不同");
        assertEquals(40, k1.length(), "sha1 十六进制 40 位");
    }

    // ==================== 3. 下发与状态机 ====================

    @Test
    @DisplayName("dispatch：PENDING → DISPATCHING → SUCCESS，逐设备写明细")
    void dispatchSuccess() {
        GrantTask t = pendingTask();
        when(taskMapper.selectById(1L)).thenReturn(t);
        when(iotClient.grant(any())).thenReturn(IotGrantResult.ok("IOT-T-1", "已受理",
                List.of(new IotGrantResult.DeviceResult("DEV-1", true, null, null, 12))));

        grantService.dispatch(1L);

        assertEquals("SUCCESS", t.getTaskStatus());
        assertEquals(1, t.getSuccessCount());
        assertEquals(0, t.getFailCount());
        assertEquals("IOT-T-1", t.getIotTaskId());
        assertNotNull(t.getFinishTime());
        verify(detailMapper, times(1)).insert(any(GrantTaskDetail.class));
    }

    @Test
    @DisplayName("dispatch：部分设备失败 → PARTIAL")
    void dispatchPartial() {
        GrantTask t = pendingTask();
        when(taskMapper.selectById(1L)).thenReturn(t);
        when(iotClient.grant(any())).thenReturn(IotGrantResult.ok("IOT-T-2", "部分成功",
                List.of(new IotGrantResult.DeviceResult("DEV-1", true, null, null, 10),
                        new IotGrantResult.DeviceResult("DEV-2", false, "99990001", "超时", 30))));

        grantService.dispatch(1L);

        assertEquals("PARTIAL", t.getTaskStatus());
        assertEquals(1, t.getSuccessCount());
        assertEquals(1, t.getFailCount());
        verify(detailMapper, times(2)).insert(any(GrantTaskDetail.class));
    }

    @Test
    @DisplayName("dispatch：全部失败 → 可重试（回到 PENDING 且 retry+1）")
    void dispatchAllFailedGoesRetry() {
        GrantTask t = pendingTask();
        when(taskMapper.selectById(1L)).thenReturn(t);
        when(iotClient.grant(any())).thenReturn(IotGrantResult.ok(null, "全部失败",
                List.of(new IotGrantResult.DeviceResult("DEV-1", false, "99990009", "解密异常", 5))));

        grantService.dispatch(1L);

        assertEquals("PENDING", t.getTaskStatus(), "未达上限应回到 PENDING 待重试");
        assertEquals(1, t.getRetryCount());
        assertNotNull(t.getLastError());
    }

    @Test
    @DisplayName("dispatch：IoT 请求本身失败 → 可重试")
    void dispatchIotRejected() {
        GrantTask t = pendingTask();
        when(taskMapper.selectById(1L)).thenReturn(t);
        when(iotClient.grant(any())).thenReturn(IotGrantResult.fail("99990002 appKey不能为空"));

        grantService.dispatch(1L);

        assertEquals("PENDING", t.getTaskStatus());
        assertEquals(1, t.getRetryCount());
        assertTrue(t.getLastError().contains("99990002"));
    }

    @Test
    @DisplayName("⭐ dispatch：重试 3 次后转 FAILED")
    void dispatchFailsAfterMaxRetry() {
        GrantTask t = pendingTask();
        t.setRetryCount(3);   // 已达上限
        when(taskMapper.selectById(1L)).thenReturn(t);

        grantService.dispatch(1L);

        assertEquals("FAILED", t.getTaskStatus());
        assertTrue(t.getLastError().contains("重试次数超过上限"));
        verify(iotClient, never()).grant(any());
    }

    @Test
    @DisplayName("dispatch 幂等：已结束的任务不重发")
    void dispatchIdempotentOnFinished() {
        GrantTask t = pendingTask();
        t.setTaskStatus("SUCCESS");
        when(taskMapper.selectById(1L)).thenReturn(t);

        grantService.dispatch(1L);

        verify(iotClient, never()).grant(any());
        verify(taskMapper, never()).updateById(any(GrantTask.class));
    }

    @Test
    @DisplayName("dispatch：任务不存在只记日志，不抛异常（避免 MQ 无限重投）")
    void dispatchMissingTask() {
        when(taskMapper.selectById(anyLong())).thenReturn(null);
        grantService.dispatch(123L);   // 不应抛异常
        verify(iotClient, never()).grant(any());
    }

    // ==================== 4. 撤销 ====================

    @Test
    @DisplayName("撤销：EFFECTIVE → REVOKED 并生成 REVOKE 任务")
    void revokeCreatesTask() {
        GrantEntitlement e = new GrantEntitlement();
        e.setId(10L);
        e.setTenantId("350600");
        e.setPersonId(5001L);
        e.setGrantStatus("EFFECTIVE");
        when(entitlementMapper.selectById(10L)).thenReturn(e);

        GrantVO vo = grantService.revoke(10L, "退租");

        assertEquals("REVOKED", vo.grantStatus());
        assertEquals("已撤销", vo.grantStatusLabel());
        ArgumentCaptor<GrantTask> tc = ArgumentCaptor.forClass(GrantTask.class);
        verify(taskMapper).insert(tc.capture());
        assertEquals("REVOKE", tc.getValue().getTaskType());
        assertEquals("PENDING", tc.getValue().getTaskStatus());
        verify(producer).publishRetry(tc.getValue().getId());
    }

    @Test
    @DisplayName("已撤销的权益不可再撤销（终态保护）")
    void revokeTerminalRejected() {
        GrantEntitlement e = new GrantEntitlement();
        e.setId(10L);
        e.setGrantStatus("REVOKED");
        when(entitlementMapper.selectById(10L)).thenReturn(e);

        BizException ex = assertThrows(BizException.class, () -> grantService.revoke(10L, "重复"));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    @Test
    @DisplayName("已到期的权益不可撤销（终态）")
    void revokeExpiredRejected() {
        GrantEntitlement e = new GrantEntitlement();
        e.setId(10L);
        e.setGrantStatus("EXPIRED");
        when(entitlementMapper.selectById(10L)).thenReturn(e);
        BizException ex = assertThrows(BizException.class, () -> grantService.revoke(10L, null));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    // ==================== 5. 状态机定义 ====================

    @Test
    @DisplayName("GrantStatus 状态机：终态不可迁移")
    void grantStatusMachine() {
        assertTrue(GrantStatus.REVOKED.isTerminal());
        assertTrue(GrantStatus.EXPIRED.isTerminal());
        assertFalse(GrantStatus.EFFECTIVE.isTerminal());
        assertTrue(GrantStatus.nextOf(GrantStatus.EFFECTIVE).contains(GrantStatus.FROZEN));
        assertTrue(GrantStatus.nextOf(GrantStatus.FROZEN).contains(GrantStatus.EFFECTIVE));
        assertTrue(GrantStatus.nextOf(GrantStatus.REVOKED).isEmpty());
    }

    @Test
    @DisplayName("GrantTaskStatus：isFinished 判定")
    void taskStatusFinished() {
        assertTrue(GrantTaskStatus.SUCCESS.isFinished());
        assertTrue(GrantTaskStatus.PARTIAL.isFinished());
        assertTrue(GrantTaskStatus.FAILED.isFinished());
        assertFalse(GrantTaskStatus.PENDING.isFinished());
        assertFalse(GrantTaskStatus.DISPATCHING.isFinished());
    }

    @Test
    @DisplayName("无租户上下文时拒绝申请")
    void applyNoTenant() {
        TenantContext.clear();
        BizException ex = assertThrows(BizException.class,
                () -> grantService.apply(cmd("USAGE", LocalDateTime.now().plusDays(1))));
        assertEquals(ErrorCode.TENANT_CONTEXT_MISSING, ex.errorCode());
    }

    private static GrantTask pendingTask() {
        GrantTask t = new GrantTask();
        t.setId(1L);
        t.setTenantId("350600");
        t.setTaskNo("T1");
        t.setTaskType("GRANT");
        t.setPersonId(5001L);
        t.setEntitlementId(100L);
        t.setTaskStatus("PENDING");
        t.setRetryCount(0);
        t.setValidStart(LocalDateTime.now());
        t.setValidEnd(LocalDateTime.now().plusDays(30));
        t.setCreateTime(LocalDateTime.now());
        return t;
    }
}
