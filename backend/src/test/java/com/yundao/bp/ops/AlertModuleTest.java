package com.yundao.bp.ops;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
import com.yundao.bp.ops.constant.AlertCategory;
import com.yundao.bp.ops.constant.AlertLevel;
import com.yundao.bp.ops.constant.AlertStatus;
import com.yundao.bp.ops.dto.AlertCreateCmd;
import com.yundao.bp.ops.dto.AlertStatsVO;
import com.yundao.bp.ops.dto.AlertVO;
import com.yundao.bp.ops.dto.WorkOrderCreateCmd;
import com.yundao.bp.ops.dto.WorkOrderVO;
import com.yundao.bp.ops.entity.OpsAlert;
import com.yundao.bp.ops.mapper.OpsAlertMapper;
import com.yundao.bp.ops.service.AlertService;
import com.yundao.bp.ops.service.WorkOrderService;
import com.yundao.bp.ops.service.impl.AlertServiceImpl;
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
 * 告警中心测试。
 *
 * <p>核心验证：
 * <ol>
 *   <li><b>状态机</b>：PENDING → HANDLING → HANDLED，误报走 IGNORED，终态不可动</li>
 *   <li><b>告警转工单</b>：���型 ALERT、SLA 按级别收紧、防重复转单</li>
 *   <li><b>统计</b>：各级别/类别/状态计数，紧急未闭环单列</li>
 * </ol>
 */
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class AlertModuleTest {

    @Mock
    private OpsAlertMapper alertMapper;
    @Mock
    private WorkOrderService workOrderService;

    private AlertService service;

    @BeforeEach
    void setUp() {
        service = new AlertServiceImpl(alertMapper, workOrderService,
                new SnowflakeIdGenerator(1, 1));
        TenantContext.set(TenantInfo.of("350600", 1001L));
        when(alertMapper.insert(any(OpsAlert.class))).thenReturn(1);
        when(alertMapper.updateById(any(OpsAlert.class))).thenReturn(1);
        when(alertMapper.selectCount(any())).thenReturn(0L);
    }

    @AfterEach
    void tearDown() {
        TenantContext.clear();
    }

    private static AlertCreateCmd cmd(String level) {
        return new AlertCreateCmd("VIOLATION", "SUBLEASE", level,
                "疑似转租转借", "同一门锁 30 天内出现 5 个不同身份证开门",
                "25%", "10%", 3001L, "RULE_SUBLEASE",
                7001L, 6001L, 5001L, 4001L, "LOCK-001", 2001L, "r1,r2,r3");
    }

    private static OpsAlert alert(String status, String level) {
        OpsAlert e = new OpsAlert();
        e.setId(1L);
        e.setTenantId("350600");
        e.setAlertNo("A1");
        e.setAlertCategory("VIOLATION");
        e.setAlertType("SUBLEASE");
        e.setAlertLevel(level);
        e.setAlertTitle("疑似转租转借");
        e.setAlertContent("同一门锁多身份证开门");
        e.setAlertStatus(status);
        e.setOrgId(7001L);
        e.setSpaceId(6001L);
        e.setHouseId(5001L);
        e.setPersonId(4001L);
        e.setDeviceId("LOCK-001");
        return e;
    }

    // ==================== 1. 创建 ====================

    @Test
    @DisplayName("创建告警：PENDING + 告警号 A 开头 + 保留阈值快照")
    void createAlert() {
        AlertVO vo = service.create(cmd("URGENT"));

        assertEquals("PENDING", vo.alertStatus());
        assertEquals("待处理", vo.alertStatusLabel());
        assertEquals("URGENT", vo.alertLevel());
        assertEquals("紧急", vo.alertLevelLabel());
        assertEquals("VIOLATION", vo.alertCategory());
        assertEquals("25%", vo.alertValue());
        assertEquals("10%", vo.thresholdValue());
        assertNotNull(vo.alertNo());
        assertTrue(vo.alertNo().startsWith("A"));

        ArgumentCaptor<OpsAlert> c = ArgumentCaptor.forClass(OpsAlert.class);
        verify(alertMapper).insert(c.capture());
        assertEquals("RULE_SUBLEASE", c.getValue().getRuleCode());
        assertEquals("r1,r2,r3", c.getValue().getRelatedIds());
        assertNotNull(c.getValue().getAlertTime());
    }

    @Test
    @DisplayName("无租户上下文时拒绝创建")
    void createNoTenant() {
        TenantContext.clear();
        BizException ex = assertThrows(BizException.class, () -> service.create(cmd("NORMAL")));
        assertEquals(ErrorCode.TENANT_CONTEXT_MISSING, ex.errorCode());
    }

    // ==================== 2. 状态机 ====================

    @Test
    @DisplayName("处置流转：PENDING → HANDLING → HANDLED")
    void handleThenResolve() {
        OpsAlert e = alert("PENDING", "IMPORTANT");
        when(alertMapper.selectById(1L)).thenReturn(e);

        assertEquals("HANDLING", service.handle(1L, 9001L, "电话联系", null).alertStatus());
        AlertVO done = service.resolve(1L, 9001L, "已核实，非转租");
        assertEquals("HANDLED", done.alertStatus());
        assertEquals("已闭环", done.alertStatusLabel());
        assertEquals("已核实，非转租", done.handleResult());
        assertNotNull(done.handleTime());
    }

    @Test
    @DisplayName("误报：PENDING → IGNORED 直通")
    void ignoreDirectly() {
        OpsAlert e = alert("PENDING", "NORMAL");
        when(alertMapper.selectById(1L)).thenReturn(e);
        AlertVO vo = service.ignore(1L, 9001L, "设备误报");
        assertEquals("IGNORED", vo.alertStatus());
        assertEquals("误报忽略", vo.alertStatusLabel());
    }

    @Test
    @DisplayName("升级：PENDING → ESCALATED，并可继续处置")
    void escalateThenHandle() {
        OpsAlert e = alert("PENDING", "URGENT");
        when(alertMapper.selectById(1L)).thenReturn(e);

        AlertVO esc = service.escalate(1L, "超时未处置，升级至项目经理");
        assertEquals("ESCALATED", esc.alertStatus());
        assertEquals("已升级", esc.alertStatusLabel());

        assertEquals("HANDLING", service.handle(1L, 9001L, "已接手", null).alertStatus());
    }

    @Test
    @DisplayName("⭐ 终态不可再流转：HANDLED 后任何操作被拒")
    void terminalCannotMove() {
        OpsAlert e = alert("HANDLED", "NORMAL");
        when(alertMapper.selectById(1L)).thenReturn(e);
        assertThrows(BizException.class, () -> service.handle(1L, 1L, null, null));
        assertThrows(BizException.class, () -> service.ignore(1L, 1L, "x"));
        assertThrows(BizException.class, () -> service.escalate(1L, "x"));
    }

    @Test
    @DisplayName("IGNORED 后不可再处置")
    void ignoredCannotMove() {
        OpsAlert e = alert("IGNORED", "NORMAL");
        when(alertMapper.selectById(1L)).thenReturn(e);
        BizException ex = assertThrows(BizException.class,
                () -> service.resolve(1L, 1L, "x"));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    @Test
    @DisplayName("重复处置被拒（已处于该状态）")
    void duplicateHandle() {
        OpsAlert e = alert("HANDLING", "NORMAL");
        when(alertMapper.selectById(1L)).thenReturn(e);
        BizException ex = assertThrows(BizException.class,
                () -> service.handle(1L, 1L, null, null));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    @Test
    @DisplayName("告警不存在报 404")
    void notFound() {
        when(alertMapper.selectById(any())).thenReturn(null);
        BizException ex = assertThrows(BizException.class, () -> service.get(999L));
        assertEquals(ErrorCode.NOT_FOUND, ex.errorCode());
    }

    // ==================== 3. 告警转工单 ====================

    @Test
    @DisplayName("⭐ 告警转工单：生成 ALERT 类型 + 紧急告警 15 分钟响应 + 回写关联")
    void toWorkOrderUrgent() {
        OpsAlert e = alert("PENDING", "URGENT");
        when(alertMapper.selectById(1L)).thenReturn(e);
        WorkOrderVO created = new WorkOrderVO(888L, "W888", "ALERT", "ALERT",
                "【告警处置】疑似转租转借", "内容", null, 7001L, 6001L, 5001L, "LOCK-001",
                4001L, null, null, null, null, "PENDING", "待派单", "ON_TIME",
                15, 120,
                false, false, null, null, null, null, null, null, null);
        when(workOrderService.create(any(WorkOrderCreateCmd.class))).thenReturn(created);

        AlertVO vo = service.toWorkOrder(1L, 9001L, "管理员");

        assertEquals(888L, vo.workorderId(), "应回写工单ID");
        assertEquals("HANDLING", vo.alertStatus(), "转单后告警进入处理中");

        ArgumentCaptor<WorkOrderCreateCmd> c =
                ArgumentCaptor.forClass(WorkOrderCreateCmd.class);
        verify(workOrderService).create(c.capture());
        WorkOrderCreateCmd wo = c.getValue();
        assertEquals("ALERT", wo.orderType());
        assertEquals("ALERT", wo.orderSource());
        assertEquals(15, wo.slaResponseMinutes(), "紧急告警响应时限 15 分钟");
        assertEquals("LOCK-001", wo.deviceId());
        assertTrue(wo.orderTitle().contains("告警处置"));
        assertTrue(wo.remark().contains("A1"), "备注应带来源告警号");
    }

    @Test
    @DisplayName("非紧急告警转工单响应时限 30 分钟")
    void toWorkOrderNormalLevel() {
        OpsAlert e = alert("PENDING", "NORMAL");
        when(alertMapper.selectById(1L)).thenReturn(e);
        when(workOrderService.create(any(WorkOrderCreateCmd.class)))
                .thenReturn(new WorkOrderVO(999L, "W999", "ALERT", "ALERT", "t", null, null,
                        null, null, null, null, null, null, null, null, null, "PENDING",
                        "待派单", "ON_TIME", 15, 120, false, false, null, null, null, null, null,
                        null, null));

        service.toWorkOrder(1L, 9001L, "管理员");
        ArgumentCaptor<WorkOrderCreateCmd> c =
                ArgumentCaptor.forClass(WorkOrderCreateCmd.class);
        verify(workOrderService).create(c.capture());
        assertEquals(30, c.getValue().slaResponseMinutes());
    }

    @Test
    @DisplayName("⭐ 防重复转单：已有 workorderId 时拒绝")
    void cannotConvertTwice() {
        OpsAlert e = alert("HANDLING", "URGENT");
        e.setWorkorderId(888L);
        when(alertMapper.selectById(1L)).thenReturn(e);

        BizException ex = assertThrows(BizException.class,
                () -> service.toWorkOrder(1L, 1L, "管理员"));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
        assertTrue(ex.getMessage().contains("已转工单"));
        verify(workOrderService, never()).create(any());
    }

    @Test
    @DisplayName("终态告警不能转工单")
    void terminalCannotConvert() {
        OpsAlert e = alert("IGNORED", "NORMAL");
        when(alertMapper.selectById(1L)).thenReturn(e);
        BizException ex = assertThrows(BizException.class,
                () -> service.toWorkOrder(1L, 1L, "管理员"));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    @Test
    @DisplayName("已升级告警转工单可直接进入处理中")
    void escalatedToWorkOrder() {
        OpsAlert e = alert("ESCALATED", "URGENT");
        when(alertMapper.selectById(1L)).thenReturn(e);
        when(workOrderService.create(any(WorkOrderCreateCmd.class)))
                .thenReturn(new WorkOrderVO(777L, "W777", "ALERT", "ALERT", "t", null, null,
                        null, null, null, null, null, null, null, null, null, "PENDING",
                        "待派单", "ON_TIME", 15, 120, false, false, null, null, null, null, null,
                        null, null));

        AlertVO vo = service.toWorkOrder(1L, 1L, "管理员");
        assertEquals("HANDLING", vo.alertStatus());
        assertEquals(777L, vo.workorderId());
    }

    // ==================== 4. 统计 ====================

    @Test
    @DisplayName("大屏统计：汇总各项计数")
    void statsAggregation() {
        // 分别对 total / PENDING / ESCALATED / HANDLING / HANDLED / IGNORED 返回不同值
        when(alertMapper.selectCount(any())).thenReturn(2L);
        AlertStatsVO s = service.stats(7001L);
        assertNotNull(s);
        assertEquals(2L, s.total());
        assertEquals(4L, s.pending(), "pending = PENDING + ESCALATED = 2 + 2");
        assertEquals(2L, s.handling());
        assertEquals(2L, s.handled());
        assertEquals(2L, s.ignored());
        assertEquals(3, s.byLevel().size());
        assertEquals(4, s.byCategory().size());
        assertTrue(s.byLevel().containsKey("URGENT"));
        assertTrue(s.byCategory().containsKey("VIOLATION"));
    }

    // ==================== 5. 枚举定义 ====================

    @Test
    @DisplayName("状态机迁移表")
    void statusMachine() {
        assertTrue(AlertStatus.nextOf(AlertStatus.PENDING).contains(AlertStatus.HANDLING));
        assertTrue(AlertStatus.nextOf(AlertStatus.PENDING).contains(AlertStatus.IGNORED));
        assertTrue(AlertStatus.nextOf(AlertStatus.ESCALATED).contains(AlertStatus.HANDLING));
        assertTrue(AlertStatus.nextOf(AlertStatus.HANDLED).isEmpty());
        assertTrue(AlertStatus.nextOf(AlertStatus.IGNORED).isEmpty());
        assertTrue(AlertStatus.HANDLED.isTerminal());
        assertFalse(AlertStatus.HANDLING.isTerminal());
        assertTrue(AlertStatus.HANDLING.isOpen());
    }

    @Test
    @DisplayName("级别权重：URGENT 最高")
    void levelWeight() {
        assertTrue(AlertLevel.URGENT.weight() < AlertLevel.IMPORTANT.weight());
        assertTrue(AlertLevel.IMPORTANT.weight() < AlertLevel.NORMAL.weight());
        assertEquals("紧急", AlertLevel.URGENT.label());
    }
}
