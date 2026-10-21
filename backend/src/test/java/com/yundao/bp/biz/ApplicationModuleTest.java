package com.yundao.bp.biz;

import com.yundao.bp.person.mapper.PersonMapper;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.yundao.bp.biz.constant.ApplicationStatus;
import com.yundao.bp.biz.constant.ReviewStage;
import com.yundao.bp.biz.dto.ApplicationCreateCmd;
import com.yundao.bp.biz.dto.ApplicationVO;
import com.yundao.bp.biz.dto.ReviewCmd;
import com.yundao.bp.biz.entity.BizApplication;
import com.yundao.bp.biz.entity.BizReviewRecord;
import com.yundao.bp.biz.mapper.BizApplicationMapper;
import com.yundao.bp.biz.mapper.BizReviewRecordMapper;
import com.yundao.bp.biz.service.ApplicationService;
import com.yundao.bp.biz.service.impl.ApplicationServiceImpl;
import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
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
 * 申请与审核测试。
 *
 * <p>核心验证：
 * <ol>
 *   <li><b>保障房必备项</b>：真实性承诺书 + 同意核实，缺一不可</li>
 *   <li><b>人均收入派生</b></li>
 *   <li><b>多阶段审核状态机</b>：非终审通过只推进阶段，终审通过才 APPROVED</li>
 *   <li><b>补件回路</b>：SUPPLEMENT → resubmit → REVIEWING</li>
 * </ol>
 */
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class ApplicationModuleTest {

    private PersonMapper personMapper;
    @Mock
    private BizApplicationMapper appMapper;
    @Mock
    private BizReviewRecordMapper reviewMapper;

    private ApplicationService service;

    @BeforeEach
    void setUp() {
        service = new ApplicationServiceImpl(appMapper, reviewMapper,
                new SnowflakeIdGenerator(1, 1), personMapper);
        TenantContext.set(TenantInfo.of("350600", 1001L));
        when(appMapper.insert(any(BizApplication.class))).thenReturn(1);
        when(appMapper.updateById(any(BizApplication.class))).thenReturn(1);
        when(reviewMapper.insert(any(BizReviewRecord.class))).thenReturn(1);
        when(reviewMapper.selectCount(any())).thenReturn(0L);
    }

    @AfterEach
    void tearDown() {
        TenantContext.clear();
    }

    private static ApplicationCreateCmd cmd(int commit, int share) {
        return new ApplicationCreateCmd(7001L, 4001L, "PUBLIC", "HOUSE", "ONLINE", 3,
                "漳州市芗城区", null, "2居", new BigDecimal("50"), new BigDecimal("70"),
                new BigDecimal("6000"), new BigDecimal("72000"), new BigDecimal("50000"),
                "LAST_YEAR", null, null, commit, share, "首次申请");
    }

    private static BizApplication app(String status) {
        BizApplication e = new BizApplication();
        e.setId(1L);
        e.setTenantId("350600");
        e.setApplicationNo("BA1");
        e.setOrgId(7001L);
        e.setPersonId(4001L);
        e.setSecurityType("PUBLIC");
        e.setApplicationStatus(status);
        e.setCurrentNode("FORM");
        return e;
    }

    // ==================== 1. 创建 ====================

    @Test
    @DisplayName("提交申请：SUBMITTED + 单号 BA 开头 + 人均收入派生")
    void createApplication() {
        ApplicationVO vo = service.create(cmd(1, 1));

        assertEquals("SUBMITTED", vo.applicationStatus());
        assertEquals("已提交", vo.applicationStatusLabel());
        assertTrue(vo.applicationNo().startsWith("BA"));
        // 6000 / 3 = 2000.00
        assertEquals(new BigDecimal("2000.00"), vo.incomePerCapita());
        assertEquals("HOUSE", vo.securityMode());
        assertNotNull(vo.applyTime());
    }

    @Test
    @DisplayName("⭐ 未签真实性承诺书 → 拒绝")
    void requireComplianceCommit() {
        BizException ex = assertThrows(BizException.class, () -> service.create(cmd(0, 1)));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
        assertTrue(ex.getMessage().contains("承诺书"));
    }

    @Test
    @DisplayName("⭐ 未同意核实 → 拒绝")
    void requireDataShareAgree() {
        BizException ex = assertThrows(BizException.class, () -> service.create(cmd(1, 0)));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
        assertTrue(ex.getMessage().contains("核实"));
    }

    @Test
    @DisplayName("意向面积区间校验")
    void areaRangeCheck() {
        ApplicationCreateCmd bad = new ApplicationCreateCmd(7001L, 4001L, "PUBLIC", "HOUSE",
                "ONLINE", 3, null, null, null,
                new BigDecimal("80"), new BigDecimal("50"),
                null, null, null, "LAST_YEAR", null, null, 1, 1, null);
        BizException ex = assertThrows(BizException.class, () -> service.create(bad));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
    }

    @Test
    @DisplayName("无租户上下文拒绝")
    void noTenant() {
        TenantContext.clear();
        BizException ex = assertThrows(BizException.class, () -> service.create(cmd(1, 1)));
        assertEquals(ErrorCode.TENANT_CONTEXT_MISSING, ex.errorCode());
    }

    // ==================== 2. 受理 ====================

    @Test
    @DisplayName("受理：SUBMITTED → REVIEWING（同时记录受理人/时间）")
    void acceptApplication() {
        BizApplication e = app("SUBMITTED");
        when(appMapper.selectById(1L)).thenReturn(e);

        ApplicationVO vo = service.accept(1L, 9001L);
        assertEquals("REVIEWING", vo.applicationStatus());
        assertEquals("审核中", vo.applicationStatusLabel());
        assertEquals(9001L, e.getAcceptUserId());
        assertNotNull(e.getAcceptTime());
    }

    @Test
    @DisplayName("跳过受理直接审核 → 拒绝")
    void cannotReviewBeforeAccept() {
        BizApplication e = app("SUBMITTED");
        when(appMapper.selectById(1L)).thenReturn(e);
        BizException ex = assertThrows(BizException.class, () -> service.review(1L,
                new ReviewCmd("ACCEPT", null, "PASS", "ok", null, null, null), 1L, "审核员"));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    // ==================== 3. 多阶段审核 ====================

    @Test
    @DisplayName("⭐ 非终审通过：只推进阶段，仍是 REVIEWING")
    void passNonFinalStageAdvances() {
        BizApplication e = app("REVIEWING");
        e.setCurrentNode("ACCEPT");
        when(appMapper.selectById(1L)).thenReturn(e);

        ApplicationVO vo = service.review(1L,
                new ReviewCmd("ACCEPT", null, "PASS", "初审通过", null, null, null),
                9001L, "审核员");

        assertEquals("REVIEWING", vo.applicationStatus());
        assertEquals("FORM", vo.currentNode(), "应推进到下一阶段");
        verify(reviewMapper, times(1)).insert(any(BizReviewRecord.class));
    }

    @Test
    @DisplayName("⭐ 终审通过 → APPROVED")
    void passFinalStageApproves() {
        BizApplication e = app("REVIEWING");
        e.setCurrentNode("JOINT");
        when(appMapper.selectById(1L)).thenReturn(e);

        ApplicationVO vo = service.review(1L,
                new ReviewCmd("FINAL", null, "PASS", "终审通过", "{\"income\":\"ok\"}",
                        null, null),
                9001L, "终审员");

        assertEquals("APPROVED", vo.applicationStatus());
        assertEquals("已通过", vo.applicationStatusLabel());
        assertEquals("DONE", vo.currentNode());

        ArgumentCaptor<BizReviewRecord> c = ArgumentCaptor.forClass(BizReviewRecord.class);
        verify(reviewMapper).insert(c.capture());
        assertEquals("FINAL", c.getValue().getReviewStage());
        assertEquals("PASS", c.getValue().getReviewResult());
        assertEquals("{\"income\":\"ok\"}", c.getValue().getCheckItems());
    }

    @Test
    @DisplayName("审核不通过 → REJECTED（终态）+ 记录原因")
    void rejectApplication() {
        BizApplication e = app("REVIEWING");
        when(appMapper.selectById(1L)).thenReturn(e);

        ApplicationVO vo = service.review(1L,
                new ReviewCmd("FORM", null, "REJECT", "材料不全", null, null, "收入超标"),
                9001L, "审核员");

        assertEquals("REJECTED", vo.applicationStatus());
        assertEquals("不通过", vo.applicationStatusLabel());
        assertEquals("收入超标", vo.rejectReason());
    }

    @Test
    @DisplayName("⭐ 需补件 → SUPPLEMENT，补件后 resubmit 回 REVIEWING")
    void supplementThenResubmit() {
        BizApplication e = app("REVIEWING");
        when(appMapper.selectById(1L)).thenReturn(e);

        ApplicationVO vo = service.review(1L,
                new ReviewCmd("FORM", null, "SUPPLEMENT", "缺收入证明", null,
                        "请补充近6个月银行流水", null),
                9001L, "审核员");
        assertEquals("SUPPLEMENT", vo.applicationStatus());
        assertEquals("待补件", vo.applicationStatusLabel());
        assertEquals("请补充近6个月银行流水", vo.supplementDemand());

        ApplicationVO re = service.resubmit(1L);
        assertEquals("REVIEWING", re.applicationStatus());
        assertNull(re.supplementDemand(), "补件要求应清空");
    }

    @Test
    @DisplayName("⭐ 待补件状态下不能直接审核")
    void cannotReviewWhileSupplement() {
        BizApplication e = app("SUPPLEMENT");
        when(appMapper.selectById(1L)).thenReturn(e);
        BizException ex = assertThrows(BizException.class, () -> service.review(1L,
                new ReviewCmd("FORM", null, "PASS", "ok", null, null, null), 1L, "审核员"));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
        assertTrue(ex.getMessage().contains("补件"));
    }

    @Test
    @DisplayName("已通过的申请不能再审核（终态）")
    void approvedCannotReview() {
        BizApplication e = app("APPROVED");
        when(appMapper.selectById(1L)).thenReturn(e);
        assertThrows(BizException.class, () -> service.review(1L,
                new ReviewCmd("FINAL", null, "PASS", "ok", null, null, null), 1L, "审核员"));
    }

    @Test
    @DisplayName("审核轮次递增")
    void reviewRoundIncrements() {
        BizApplication e = app("REVIEWING");
        when(appMapper.selectById(1L)).thenReturn(e);
        when(reviewMapper.selectCount(any())).thenReturn(2L);

        service.review(1L, new ReviewCmd("JOINT", "REAL_ESTATE", "PASS", "ok", null, null, null),
                9001L, "审核员");

        ArgumentCaptor<BizReviewRecord> c = ArgumentCaptor.forClass(BizReviewRecord.class);
        verify(reviewMapper).insert(c.capture());
        assertEquals(3, c.getValue().getReviewRound(), "已有 2 条 → 本轮为第 3 轮");
        assertEquals("REAL_ESTATE", c.getValue().getReviewDept());
    }

    // ==================== 4. 撤回 ====================

    @Test
    @DisplayName("已提交可撤回")
    void cancelSubmitted() {
        BizApplication e = app("SUBMITTED");
        when(appMapper.selectById(1L)).thenReturn(e);
        assertEquals("CANCELLED", service.cancel(1L, "不再申请").applicationStatus());
    }

    @Test
    @DisplayName("⭐ 已进入审核不可撤回")
    void cannotCancelInReview() {
        BizApplication e = app("REVIEWING");
        when(appMapper.selectById(1L)).thenReturn(e);
        BizException ex = assertThrows(BizException.class, () -> service.cancel(1L, "撤回"));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
        assertTrue(ex.getMessage().contains("不可撤回"));
    }

    @Test
    @DisplayName("申请不存在报 404")
    void notFound() {
        when(appMapper.selectById(any())).thenReturn(null);
        BizException ex = assertThrows(BizException.class, () -> service.get(999L));
        assertEquals(ErrorCode.NOT_FOUND, ex.errorCode());
    }

    // ==================== 5. 状态机与阶段定义 ====================

    @Test
    @DisplayName("申请状态机定义")
    void statusMachine() {
        assertTrue(ApplicationStatus.nextOf(ApplicationStatus.DRAFT)
                .contains(ApplicationStatus.SUBMITTED));
        assertFalse(ApplicationStatus.nextOf(ApplicationStatus.DRAFT)
                .contains(ApplicationStatus.APPROVED));
        assertTrue(ApplicationStatus.nextOf(ApplicationStatus.SUPPLEMENT)
                .contains(ApplicationStatus.REVIEWING));
        assertTrue(ApplicationStatus.nextOf(ApplicationStatus.APPROVED).isEmpty());
        assertTrue(ApplicationStatus.APPROVED.isTerminal());
        assertTrue(ApplicationStatus.REVIEWING.isInReview());
        assertFalse(ApplicationStatus.SUBMITTED.isInReview());
    }

    @Test
    @DisplayName("审核阶段链：ACCEPT → FORM → JOINT → FINAL")
    void reviewStageChain() {
        assertEquals(ReviewStage.FORM, ReviewStage.ACCEPT.next());
        assertEquals(ReviewStage.JOINT, ReviewStage.FORM.next());
        assertEquals(ReviewStage.FINAL, ReviewStage.JOINT.next());
        assertNull(ReviewStage.FINAL.next());
        assertTrue(ReviewStage.FINAL.isLast());
        assertFalse(ReviewStage.ACCEPT.isLast());
    }
}
