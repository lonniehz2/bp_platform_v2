package com.yundao.bp.ops;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
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
import com.yundao.bp.ops.constant.SlaStatus;
import com.yundao.bp.ops.constant.WorkOrderStatus;
import com.yundao.bp.ops.dto.WorkOrderCreateCmd;
import com.yundao.bp.ops.dto.WorkOrderVO;
import com.yundao.bp.ops.entity.OpsWorkorder;
import com.yundao.bp.ops.entity.OpsWorkorderLog;
import com.yundao.bp.ops.mapper.OpsWorkorderLogMapper;
import com.yundao.bp.ops.mapper.OpsWorkorderMapper;
import com.yundao.bp.ops.service.WorkOrderService;
import com.yundao.bp.ops.service.impl.WorkOrderServiceImpl;
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
 * 工单模块测试。
 *
 * <p>核心验证：
 * <ol>
 *   <li><b>状态机不可跳步</b>（不能"待派单"直接"闭环"）</li>
 *   <li><b>全留痕</b>：每次流转都写 log</li>
 *   <li><b>SLA 判定</b>：响应/完工超时的口径</li>
 *   <li><b>默认 SLA</b>按工单类型取值</li>
 * </ol>
 */
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class WorkOrderModuleTest {

    @Mock
    private OpsWorkorderMapper orderMapper;
    @Mock
    private OpsWorkorderLogMapper logMapper;

    private WorkOrderService service;

    @BeforeEach
    void setUp() {
        service = new WorkOrderServiceImpl(orderMapper, logMapper,
                new SnowflakeIdGenerator(1, 1));
        TenantContext.set(TenantInfo.of("350600", 1001L));
        when(orderMapper.insert(any(OpsWorkorder.class))).thenReturn(1);
        when(orderMapper.updateById(any(OpsWorkorder.class))).thenReturn(1);
        when(logMapper.insert(any(OpsWorkorderLog.class))).thenReturn(1);
    }

    @AfterEach
    void tearDown() {
        TenantContext.clear();
    }

    private static WorkOrderCreateCmd cmd(String type) {
        return new WorkOrderCreateCmd(type, "STAFF", "101室门锁无法开门", "刷卡无反应",
                7001L, 6001L, 5001L, "LOCK-001", "LOCK", 4001L, "张三", "13800138000",
                "1幢1单元1层101室", null, null, null, "加急");
    }

    private static OpsWorkorder order(String status, int respondMin, int finishMin,
                                      LocalDateTime createTime) {
        OpsWorkorder e = new OpsWorkorder();
        e.setId(1L);
        e.setTenantId("350600");
        e.setWorkorderNo("W1");
        e.setOrderType("REPAIR");
        e.setOrderStatus(status);
        e.setSlaResponseMinutes(respondMin);
        e.setSlaFinishMinutes(finishMin);
        e.setCreateTime(createTime);
        return e;
    }

    // ==================== 1. 创建 ====================

    @Test
    @DisplayName("创建工单：初始 PENDING + 按类型取默认 SLA + 写创建日志")
    void createWithDefaultSla() {
        WorkOrderVO vo = service.create(cmd("REPAIR"));

        assertEquals("PENDING", vo.orderStatus());
        assertEquals("待派单", vo.orderStatusLabel());
        assertEquals("ON_TIME", vo.slaStatus());
        assertNotNull(vo.workorderNo());
        assertTrue(vo.workorderNo().startsWith("W"));

        ArgumentCaptor<OpsWorkorder> oc = ArgumentCaptor.forClass(OpsWorkorder.class);
        verify(orderMapper).insert(oc.capture());
        // REPAIR 默认 30 分钟响应 / 240 分钟完工
        assertEquals(30, oc.getValue().getSlaResponseMinutes());
        assertEquals(240, oc.getValue().getSlaFinishMinutes());
        assertEquals(0, oc.getValue().getIsDeviceChanged());

        ArgumentCaptor<OpsWorkorderLog> lc = ArgumentCaptor.forClass(OpsWorkorderLog.class);
        verify(logMapper).insert(lc.capture());
        assertEquals("CREATE", lc.getValue().getAction());
        assertEquals("PENDING", lc.getValue().getToStatus());
    }

    @Test
    @DisplayName("告警转工单：ALERT 类型默认 15 分钟响应（更紧急）")
    void alertTypeHasTighterSla() {
        WorkOrderVO vo = service.create(cmd("ALERT"));
        ArgumentCaptor<OpsWorkorder> oc = ArgumentCaptor.forClass(OpsWorkorder.class);
        verify(orderMapper).insert(oc.capture());
        assertEquals(15, oc.getValue().getSlaResponseMinutes());
        assertEquals(120, oc.getValue().getSlaFinishMinutes());
        assertEquals("ALERT", vo.orderType());
    }

    @Test
    @DisplayName("可显式覆盖 SLA 时限")
    void customSla() {
        WorkOrderCreateCmd c = new WorkOrderCreateCmd("REPAIR", "PHONE", "测试", null,
                null, null, null, null, null, null, null, null, null, null,
                10, 60, null);
        service.create(c);
        ArgumentCaptor<OpsWorkorder> oc = ArgumentCaptor.forClass(OpsWorkorder.class);
        verify(orderMapper).insert(oc.capture());
        assertEquals(10, oc.getValue().getSlaResponseMinutes());
        assertEquals(60, oc.getValue().getSlaFinishMinutes());
    }

    @Test
    @DisplayName("SLA 时限必须为正数")
    void invalidSlaRejected() {
        WorkOrderCreateCmd c = new WorkOrderCreateCmd("REPAIR", "PHONE", "测试", null,
                null, null, null, null, null, null, null, null, null, null,
                0, 60, null);
        BizException ex = assertThrows(BizException.class, () -> service.create(c));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
    }

    @Test
    @DisplayName("无租户上下文时拒绝创建")
    void createNoTenant() {
        TenantContext.clear();
        BizException ex = assertThrows(BizException.class, () -> service.create(cmd("REPAIR")));
        assertEquals(ErrorCode.TENANT_CONTEXT_MISSING, ex.errorCode());
    }

    // ==================== 2. 完整闭环 ====================

    @Test
    @DisplayName("完整闭环：PENDING→ASSIGNED→ACCEPTED→PROCESSING→FINISHED→CLOSED")
    void fullLifecycle() {
        OpsWorkorder e = order("PENDING", 30, 240, LocalDateTime.now().minusMinutes(5));
        when(orderMapper.selectById(1L)).thenReturn(e);

        assertEquals("ASSIGNED", service.assign(1L, 9001L, "李师傅", "13900139000", "派单").orderStatus());
        assertEquals("ACCEPTED", service.accept(1L, 9001L, "李师傅", "收到").orderStatus());
        assertEquals("PROCESSING", service.start(1L, 9001L, "李师傅", "已出发").orderStatus());
        assertEquals("FINISHED", service.finish(1L, 9001L, "李师傅", "更换电池", "已修复").orderStatus());
        WorkOrderVO closed = service.close(1L, 9001L, "管理员", "确认闭环");
        assertEquals("CLOSED", closed.orderStatus());
        assertEquals("已闭环", closed.orderStatusLabel());

        assertNotNull(closed.assignTime());
        assertNotNull(closed.acceptTime());
        assertNotNull(closed.finishTime());
        assertNotNull(closed.closeTime());

        // 本用例未走 create()（工单是预置的），故只有 5 次流转 = 5 条日志
        verify(logMapper, times(5)).insert(any(OpsWorkorderLog.class));
    }

    @Test
    @DisplayName("⭐ 状态机不可跳步：PENDING 不能直接闭环")
    void cannotSkipSteps() {
        OpsWorkorder e = order("PENDING", 30, 240, LocalDateTime.now());
        when(orderMapper.selectById(1L)).thenReturn(e);

        BizException ex = assertThrows(BizException.class,
                () -> service.close(1L, 1L, "管理员", "直接闭环"));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
        assertTrue(ex.getMessage().contains("不允许"), ex.getMessage());
    }

    @Test
    @DisplayName("⭐ 状态机不可跳步：ASSIGNED 不能直接完工")
    void cannotFinishFromAssigned() {
        OpsWorkorder e = order("ASSIGNED", 30, 240, LocalDateTime.now());
        when(orderMapper.selectById(1L)).thenReturn(e);
        BizException ex = assertThrows(BizException.class,
                () -> service.finish(1L, 1L, "李师傅", "修好", null));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    @Test
    @DisplayName("终态不可再流转：CLOSED 后任何操作都被拒")
    void terminalCannotMove() {
        OpsWorkorder e = order("CLOSED", 30, 240, LocalDateTime.now());
        when(orderMapper.selectById(1L)).thenReturn(e);
        assertThrows(BizException.class, () -> service.cancel(1L, 1L, "管理员", "取消"));
        assertThrows(BizException.class, () -> service.accept(1L, 1L, "李师傅", null));
    }

    @Test
    @DisplayName("重复接单被拒（已处于该状态）")
    void duplicateAccept() {
        OpsWorkorder e = order("ACCEPTED", 30, 240, LocalDateTime.now());
        when(orderMapper.selectById(1L)).thenReturn(e);
        BizException ex = assertThrows(BizException.class,
                () -> service.accept(1L, 1L, "李师傅", null));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    @Test
    @DisplayName("派单必须指定处理人")
    void assignRequiresUser() {
        OpsWorkorder e = order("PENDING", 30, 240, LocalDateTime.now());
        when(orderMapper.selectById(1L)).thenReturn(e);
        BizException ex = assertThrows(BizException.class,
                () -> service.assign(1L, null, "李师傅", null, null));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
    }

    @Test
    @DisplayName("工单不存在报 404")
    void notFound() {
        when(orderMapper.selectById(any())).thenReturn(null);
        BizException ex = assertThrows(BizException.class, () -> service.get(999L));
        assertEquals(ErrorCode.NOT_FOUND, ex.errorCode());
    }

    // ==================== 3. SLA ====================

    @Test
    @DisplayName("响应按时：20 分钟接单（限 30 分钟）→ ON_TIME")
    void responseOnTime() {
        OpsWorkorder e = order("ASSIGNED", 30, 240, LocalDateTime.now().minusMinutes(20));
        when(orderMapper.selectById(1L)).thenReturn(e);

        WorkOrderVO vo = service.accept(1L, 1L, "李师傅", null);
        assertEquals(SlaStatus.ON_TIME.name(), vo.slaStatus());
    }

    @Test
    @DisplayName("⭐ 响应超时：40 分钟接单（限 30 分钟）→ RESPONSE_TIMEOUT")
    void responseTimeout() {
        OpsWorkorder e = order("ASSIGNED", 30, 240, LocalDateTime.now().minusMinutes(40));
        when(orderMapper.selectById(1L)).thenReturn(e);

        WorkOrderVO vo = service.accept(1L, 1L, "李师傅", null);
        assertEquals(SlaStatus.RESPONSE_TIMEOUT.name(), vo.slaStatus());
    }

    @Test
    @DisplayName("⭐ 完工超时：300 分钟完工（限 240 分钟）→ FINISH_TIMEOUT")
    void finishTimeout() {
        OpsWorkorder e = order("PROCESSING", 30, 240, LocalDateTime.now().minusMinutes(300));
        e.setAcceptTime(LocalDateTime.now().minusMinutes(295));
        when(orderMapper.selectById(1L)).thenReturn(e);

        WorkOrderVO vo = service.finish(1L, 1L, "李师傅", "已修复", null);
        assertEquals(SlaStatus.FINISH_TIMEOUT.name(), vo.slaStatus());
    }

    @Test
    @DisplayName("完工按时：100 分钟完工（限 240 分钟）→ ON_TIME")
    void finishOnTime() {
        OpsWorkorder e = order("PROCESSING", 30, 240, LocalDateTime.now().minusMinutes(100));
        when(orderMapper.selectById(1L)).thenReturn(e);
        WorkOrderVO vo = service.finish(1L, 1L, "李师傅", "已修复", null);
        // 完工按时不应覆盖已有的响应超时（更严重信息保留）
        assertTrue(SlaStatus.ON_TIME.name().equals(vo.slaStatus())
                || SlaStatus.RESPONSE_TIMEOUT.name().equals(vo.slaStatus()));
    }

    @Test
    @DisplayName("派生指标：未接单且超响应时限 → responseOverdue=true")
    void responseOverdueDerived() {
        OpsWorkorder e = order("ASSIGNED", 30, 240, LocalDateTime.now().minusMinutes(40));
        when(orderMapper.selectById(1L)).thenReturn(e);
        WorkOrderVO vo = service.get(1L);
        assertTrue(vo.responseOverdue(), "应判为响应超时");
        assertFalse(vo.finishOverdue(), "完工时限 240 分钟还没到");
    }

    @Test
    @DisplayName("派生指标：已接单后不再判响应超时")
    void noResponseOverdueAfterAccept() {
        OpsWorkorder e = order("ACCEPTED", 30, 240, LocalDateTime.now().minusMinutes(40));
        e.setAcceptTime(LocalDateTime.now().minusMinutes(35));
        when(orderMapper.selectById(1L)).thenReturn(e);
        assertFalse(service.get(1L).responseOverdue());
    }

    @Test
    @DisplayName("派生指标：终态工单不再判超时")
    void noOverdueForTerminal() {
        OpsWorkorder e = order("CLOSED", 30, 240, LocalDateTime.now().minusMinutes(1000));
        when(orderMapper.selectById(1L)).thenReturn(e);
        WorkOrderVO vo = service.get(1L);
        assertFalse(vo.responseOverdue());
        assertFalse(vo.finishOverdue());
    }

    // ==================== 4. 状态机定义 ====================

    @Test
    @DisplayName("状态机迁移表完整性")
    void statusMachineDefinition() {
        assertTrue(WorkOrderStatus.nextOf(WorkOrderStatus.PENDING)
                .contains(WorkOrderStatus.ASSIGNED));
        assertTrue(WorkOrderStatus.nextOf(WorkOrderStatus.FINISHED)
                .contains(WorkOrderStatus.CLOSED));
        assertFalse(WorkOrderStatus.nextOf(WorkOrderStatus.PENDING)
                .contains(WorkOrderStatus.CLOSED), "PENDING 不可直达 CLOSED");
        assertTrue(WorkOrderStatus.nextOf(WorkOrderStatus.CLOSED).isEmpty());
        assertTrue(WorkOrderStatus.nextOf(WorkOrderStatus.REJECTED).isEmpty());
        assertTrue(WorkOrderStatus.CLOSED.isTerminal());
        assertTrue(WorkOrderStatus.PROCESSING.isOpen());
        assertEquals("待派单", WorkOrderStatus.PENDING.label());
    }

    @Test
    @DisplayName("IN_PROGRESS 集合用于待办统计")
    void inProgressSet() {
        assertEquals(3, WorkOrderStatus.IN_PROGRESS.size());
        assertTrue(WorkOrderStatus.IN_PROGRESS.contains(WorkOrderStatus.ASSIGNED));
        assertFalse(WorkOrderStatus.IN_PROGRESS.contains(WorkOrderStatus.PENDING));
    }
}
