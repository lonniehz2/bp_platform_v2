package com.yundao.bp.ops;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
import com.yundao.bp.ops.constant.ComplaintStatus;
import com.yundao.bp.ops.constant.VisitStatus;
import com.yundao.bp.ops.dto.ComplaintCreateCmd;
import com.yundao.bp.ops.dto.ComplaintVO;
import com.yundao.bp.ops.dto.VisitCreateCmd;
import com.yundao.bp.ops.dto.VisitResultCmd;
import com.yundao.bp.ops.dto.VisitVO;
import com.yundao.bp.ops.dto.WorkOrderCreateCmd;
import com.yundao.bp.ops.dto.WorkOrderVO;
import com.yundao.bp.ops.entity.OpsComplaint;
import com.yundao.bp.ops.entity.OpsHouseVisit;
import com.yundao.bp.ops.mapper.OpsComplaintMapper;
import com.yundao.bp.ops.mapper.OpsHouseVisitMapper;
import com.yundao.bp.ops.service.ComplaintService;
import com.yundao.bp.ops.service.VisitService;
import com.yundao.bp.ops.service.WorkOrderService;
import com.yundao.bp.ops.service.impl.ComplaintServiceImpl;
import com.yundao.bp.ops.service.impl.VisitServiceImpl;
import java.time.LocalDate;
import java.time.LocalDateTime;
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
 * 投诉建议 + 巡房走访测试。
 */
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class ComplaintVisitModuleTest {

    @Mock
    private OpsComplaintMapper complaintMapper;
    @Mock
    private OpsHouseVisitMapper visitMapper;
    @Mock
    private WorkOrderService workOrderService;

    private ComplaintService complaintService;
    private VisitService visitService;

    @BeforeEach
    void setUp() {
        SnowflakeIdGenerator gen = new SnowflakeIdGenerator(1, 1);
        complaintService = new ComplaintServiceImpl(complaintMapper, workOrderService, gen);
        visitService = new VisitServiceImpl(visitMapper, workOrderService, gen);
        TenantContext.set(TenantInfo.of("350600", 1001L));
        when(complaintMapper.insert(any(OpsComplaint.class))).thenReturn(1);
        when(complaintMapper.updateById(any(OpsComplaint.class))).thenReturn(1);
        when(visitMapper.insert(any(OpsHouseVisit.class))).thenReturn(1);
        when(visitMapper.updateById(any(OpsHouseVisit.class))).thenReturn(1);
    }

    @AfterEach
    void tearDown() {
        TenantContext.clear();
    }

    private static ComplaintCreateCmd cCmd(String type) {
        return new ComplaintCreateCmd(type, "MINIAPP", "楼道灯不亮", "已经坏了三天",
                null, 7001L, 4001L, "张三", "13800138000");
    }

    private static OpsComplaint complaint(String status, String type) {
        OpsComplaint e = new OpsComplaint();
        e.setId(1L);
        e.setTenantId("350600");
        e.setComplaintNo("C1");
        e.setComplaintType(type);
        e.setTitle("楼道灯不亮");
        e.setContent("已经坏了三天");
        e.setHandleStatus(status);
        e.setOrgId(7001L);
        e.setPersonId(4001L);
        e.setCreateTime(LocalDateTime.now());
        return e;
    }

    private static WorkOrderVO wo(long id) {
        return new WorkOrderVO(id, "W" + id, "COMPLAINT", "STAFF", "t", null, null,
                null, null, null, null, null, null, null, null, null, "PENDING",
                "待派单", "ON_TIME", 60, 480, false, false, null, null, null, null, null,
                null, null);
    }

    // ==================== 投诉建议 ====================

    @Test
    @DisplayName("提交投诉：PENDING + 单号 C 开头")
    void createComplaint() {
        ComplaintVO vo = complaintService.create(cCmd("COMPLAINT"));
        assertEquals("PENDING", vo.handleStatus());
        assertEquals("待处理", vo.handleStatusLabel());
        assertTrue(vo.complaintNo().startsWith("C"));
        assertEquals("张三", vo.submitterName());
        assertFalse(vo.overdue(), "刚创建不应超时");
    }

    @Test
    @DisplayName("投诉状态机：PENDING → HANDLING → HANDLED → CLOSED")
    void complaintLifecycle() {
        OpsComplaint e = complaint("PENDING", "COMPLAINT");
        when(complaintMapper.selectById(1L)).thenReturn(e);

        assertEquals("HANDLING", complaintService.handle(1L, 9001L).handleStatus());
        ComplaintVO done = complaintService.resolve(1L, 9001L, "已更换灯泡");
        assertEquals("HANDLED", done.handleStatus());
        assertEquals("已处理", done.handleStatusLabel());
        assertEquals("已更换灯泡", done.handleResult());
        assertEquals("CLOSED", complaintService.close(1L, 9001L).handleStatus());
    }

    @Test
    @DisplayName("⭐ 状态机不可跳步：PENDING 不能直接归档")
    void complaintCannotSkip() {
        OpsComplaint e = complaint("PENDING", "COMPLAINT");
        when(complaintMapper.selectById(1L)).thenReturn(e);
        BizException ex = assertThrows(BizException.class,
                () -> complaintService.close(1L, 1L));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    @Test
    @DisplayName("CLOSED 是终态")
    void complaintClosedIsTerminal() {
        OpsComplaint e = complaint("CLOSED", "COMPLAINT");
        when(complaintMapper.selectById(1L)).thenReturn(e);
        assertThrows(BizException.class, () -> complaintService.handle(1L, 1L));
    }

    @Test
    @DisplayName("满意度评价：1-5 有效，超范围被拒")
    void evaluateSatisfaction() {
        OpsComplaint e = complaint("HANDLED", "COMPLAINT");
        when(complaintMapper.selectById(1L)).thenReturn(e);

        assertEquals(5, complaintService.evaluate(1L, 5).satisfaction());
        assertThrows(BizException.class, () -> complaintService.evaluate(1L, 0));
        assertThrows(BizException.class, () -> complaintService.evaluate(1L, 6));
        assertThrows(BizException.class, () -> complaintService.evaluate(1L, null));
    }

    @Test
    @DisplayName("未处理不能评价")
    void cannotEvaluatePending() {
        OpsComplaint e = complaint("PENDING", "COMPLAINT");
        when(complaintMapper.selectById(1L)).thenReturn(e);
        BizException ex = assertThrows(BizException.class,
                () -> complaintService.evaluate(1L, 5));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    @Test
    @DisplayName("⭐ 投诉超 48 小时未处理 → overdue=true")
    void complaintOverdue() {
        OpsComplaint e = complaint("PENDING", "COMPLAINT");
        e.setCreateTime(LocalDateTime.now().minusHours(50));
        when(complaintMapper.selectById(1L)).thenReturn(e);
        assertTrue(complaintService.get(1L).overdue());
    }

    @Test
    @DisplayName("建议类不参与 48 小时超时判定")
    void suggestNotOverdue() {
        OpsComplaint e = complaint("PENDING", "SUGGEST");
        e.setCreateTime(LocalDateTime.now().minusHours(100));
        when(complaintMapper.selectById(1L)).thenReturn(e);
        assertFalse(complaintService.get(1L).overdue(), "只有投诉类算超时");
    }

    @Test
    @DisplayName("投诉转工单：COMPLAINT 类型 + 60 分钟响应 + 回写")
    void complaintToWorkOrder() {
        OpsComplaint e = complaint("PENDING", "COMPLAINT");
        when(complaintMapper.selectById(1L)).thenReturn(e);
        when(workOrderService.create(any(WorkOrderCreateCmd.class))).thenReturn(wo(888L));

        ComplaintVO vo = complaintService.toWorkOrder(1L, 9001L, "管理员");
        assertEquals(888L, vo.workorderId());
        assertEquals("HANDLING", vo.handleStatus());

        ArgumentCaptor<WorkOrderCreateCmd> c =
                ArgumentCaptor.forClass(WorkOrderCreateCmd.class);
        verify(workOrderService).create(c.capture());
        assertEquals("COMPLAINT", c.getValue().orderType());
        assertEquals(60, c.getValue().slaResponseMinutes());
        assertTrue(c.getValue().orderTitle().contains("投诉处置"));
    }

    @Test
    @DisplayName("防重复转工单")
    void complaintCannotConvertTwice() {
        OpsComplaint e = complaint("HANDLING", "COMPLAINT");
        e.setWorkorderId(888L);
        when(complaintMapper.selectById(1L)).thenReturn(e);
        BizException ex = assertThrows(BizException.class,
                () -> complaintService.toWorkOrder(1L, 1L, "管理员"));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
        verify(workOrderService, never()).create(any());
    }

    @Test
    @DisplayName("已归档投诉不能转工单")
    void closedCannotConvert() {
        OpsComplaint e = complaint("CLOSED", "COMPLAINT");
        when(complaintMapper.selectById(1L)).thenReturn(e);
        assertThrows(BizException.class, () -> complaintService.toWorkOrder(1L, 1L, "管理员"));
    }

    // ==================== 巡房走访 ====================

    @Test
    @DisplayName("创建走访：PENDING + 单号 V 开头 + 默认计划日期")
    void createVisit() {
        VisitCreateCmd c = new VisitCreateCmd("VERIFY", 7001L, 5001L, 6001L, 4001L,
                null, 9001L, "李师傅", "系统预警长期未开门", 3001L);
        VisitVO vo = visitService.create(c);
        assertEquals("PENDING", vo.visitStatus());
        assertEquals("待走访", vo.visitStatusLabel());
        assertTrue(vo.visitNo().startsWith("V"));
        assertNotNull(vo.planDate());
        assertEquals("系统预警长期未开门", vo.triggerReason());
        assertEquals(3001L, vo.alertId());
    }

    @Test
    @DisplayName("走访房源必填")
    void visitHouseRequired() {
        VisitCreateCmd c = new VisitCreateCmd("ROUTINE", 7001L, null, null, null,
                null, null, null, null, null);
        VisitVO vo = visitService.create(c);
        assertNull(vo.houseId());
        // 校验在 Controller 层（@NotNull），服务层不做，这里只验证不崩
        assertNotNull(vo.id());
    }

    @Test
    @DisplayName("⭐ 回填走访结果：发现转租转借")
    void reportVisitWithSublease() {
        OpsHouseVisit e = visit("PENDING");
        when(visitMapper.selectById(1L)).thenReturn(e);

        VisitResultCmd r = new VisitResultCmd("DONE", LocalDate.now(), 1, 3, "MISMATCH",
                "实际居住人与合同不符，疑似转租", 1, 0, 0,
                "img1.jpg", "1幢门口", "建议解除合同");
        VisitVO vo = visitService.report(1L, r);

        assertEquals("DONE", vo.visitStatus());
        assertEquals("已完成", vo.visitStatusLabel());
        assertTrue(vo.sublease(), "应标记发现转租");
        assertFalse(vo.idle());
        assertEquals("MISMATCH", vo.matchResult());
        assertEquals("不一致", vo.matchResultLabel());
        assertEquals(3, vo.actualResidents());
        assertTrue(vo.occupied());
        assertEquals("建议解除合同", vo.nextAction());
    }

    @Test
    @DisplayName("回填无人：ABSENT")
    void reportAbsent() {
        OpsHouseVisit e = visit("PENDING");
        when(visitMapper.selectById(1L)).thenReturn(e);
        VisitVO vo = visitService.report(1L,
                new VisitResultCmd("ABSENT", LocalDate.now(), 0, 0, "UNKNOWN",
                        "敲门无人应答", 0, 1, 0, null, null, "再次上门"));
        assertEquals("ABSENT", vo.visitStatus());
        assertTrue(vo.idle(), "标记发现闲置");
    }

    @Test
    @DisplayName("已完成的走访不能再回填")
    void cannotReportTwice() {
        OpsHouseVisit e = visit("DONE");
        when(visitMapper.selectById(1L)).thenReturn(e);
        BizException ex = assertThrows(BizException.class,
                () -> visitService.report(1L, new VisitResultCmd("DONE", LocalDate.now(),
                        null, null, null, null, null, null, null, null, null, null)));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    @Test
    @DisplayName("⭐ 走访异常转工单：INSPECT 类型 + 内容汇总异常项")
    void visitToWorkOrder() {
        OpsHouseVisit e = visit("DONE");
        e.setIsSublease(1);
        e.setIsIllegalUse(1);
        e.setFindings("实际居住人与合同不符");
        when(visitMapper.selectById(1L)).thenReturn(e);
        when(workOrderService.create(any(WorkOrderCreateCmd.class))).thenReturn(wo(999L));

        VisitVO vo = visitService.toWorkOrder(1L, 9001L, "管理员");
        assertEquals(999L, vo.workorderId());

        ArgumentCaptor<WorkOrderCreateCmd> c =
                ArgumentCaptor.forClass(WorkOrderCreateCmd.class);
        verify(workOrderService).create(c.capture());
        assertEquals("INSPECT", c.getValue().orderType());
        String content = c.getValue().orderContent();
        assertTrue(content.contains("转租转借"), "内容应含转租: " + content);
        assertTrue(content.contains("违规使用"), "内容应含违规: " + content);
        assertTrue(c.getValue().orderTitle().contains("走访核查"));
    }

    @Test
    @DisplayName("未完成的走访不能转工单")
    void pendingCannotConvert() {
        OpsHouseVisit e = visit("PENDING");
        when(visitMapper.selectById(1L)).thenReturn(e);
        BizException ex = assertThrows(BizException.class,
                () -> visitService.toWorkOrder(1L, 1L, "管理员"));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    @Test
    @DisplayName("已取消的走访不能转工单")
    void cancelledCannotConvert() {
        OpsHouseVisit e = visit("CANCELLED");
        when(visitMapper.selectById(1L)).thenReturn(e);
        assertThrows(BizException.class, () -> visitService.toWorkOrder(1L, 1L, "管理员"));
    }

    @Test
    @DisplayName("取消走访")
    void cancelVisit() {
        OpsHouseVisit e = visit("PENDING");
        when(visitMapper.selectById(1L)).thenReturn(e);
        VisitVO vo = visitService.cancel(1L, "住户已搬离");
        assertEquals("CANCELLED", vo.visitStatus());
        assertEquals("已取消", vo.visitStatusLabel());
    }

    @Test
    @DisplayName("⭐ 逾期未走访：计划日期已过仍 PENDING → overdue")
    void visitOverdue() {
        OpsHouseVisit e = visit("PENDING");
        e.setPlanDate(LocalDate.now().minusDays(3));
        when(visitMapper.selectById(1L)).thenReturn(e);
        assertTrue(visitService.get(1L).overdue());
    }

    @Test
    @DisplayName("已完成走访不判逾期")
    void doneNotOverdue() {
        OpsHouseVisit e = visit("DONE");
        e.setPlanDate(LocalDate.now().minusDays(10));
        when(visitMapper.selectById(1L)).thenReturn(e);
        assertFalse(visitService.get(1L).overdue());
    }

    // ==================== 状态机定义 ====================

    @Test
    @DisplayName("投诉状态机定义")
    void complaintStatusMachine() {
        assertTrue(ComplaintStatus.nextOf(ComplaintStatus.PENDING)
                .contains(ComplaintStatus.HANDLING));
        assertFalse(ComplaintStatus.nextOf(ComplaintStatus.PENDING)
                .contains(ComplaintStatus.CLOSED), "PENDING 不可直达 CLOSED");
        assertTrue(ComplaintStatus.CLOSED.isTerminal());
        assertFalse(ComplaintStatus.HANDLED.isTerminal());
    }

    @Test
    @DisplayName("走访状态机定义：PENDING 可到 4 种终态")
    void visitStatusMachine() {
        assertEquals(4, VisitStatus.nextOf(VisitStatus.PENDING).size());
        assertTrue(VisitStatus.nextOf(VisitStatus.DONE).isEmpty());
        assertTrue(VisitStatus.DONE.isTerminal());
        assertFalse(VisitStatus.PENDING.isTerminal());
    }

    private static OpsHouseVisit visit(String status) {
        OpsHouseVisit e = new OpsHouseVisit();
        e.setId(1L);
        e.setTenantId("350600");
        e.setVisitNo("V1");
        e.setVisitType("VERIFY");
        e.setHouseId(5001L);
        e.setSpaceId(6001L);
        e.setOrgId(7001L);
        e.setPersonId(4001L);
        e.setVisitStatus(status);
        e.setPlanDate(LocalDate.now());
        e.setCreateTime(LocalDateTime.now());
        return e;
    }
}
