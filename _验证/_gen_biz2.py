# -*- coding: utf-8 -*-
"""生成 biz 业务办理（第 2 部分：服务/控制器）"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['biz/service/ApplicationService.java'] = '''package com.yundao.bp.biz.service;

import com.yundao.bp.biz.dto.ApplicationCreateCmd;
import com.yundao.bp.biz.dto.ApplicationVO;
import com.yundao.bp.biz.dto.ReviewCmd;
import com.yundao.bp.biz.entity.BizReviewRecord;
import com.yundao.bp.common.api.PageResult;
import java.util.List;

/**
 * 保障房申请与审核服务。
 *
 * <p>流程：提交 → 受理 → 审核中 →（通过 / 不通过 / 需补件）→ 补件后回到审核中 → 通过。
 */
public interface ApplicationService {

    ApplicationVO create(ApplicationCreateCmd cmd);

    ApplicationVO get(Long id);

    PageResult<ApplicationVO> page(long pageNum, long pageSize, String securityType,
                                   String status, Long orgId, String keyword);

    /** 受理：SUBMITTED → ACCEPTED。 */
    ApplicationVO accept(Long id, Long acceptUserId);

    /** 提交审核结果（按阶段推进状态机）。 */
    ApplicationVO review(Long id, ReviewCmd cmd, Long reviewUserId, String reviewUserName);

    /** 退回补件后重新提交：SUPPLEMENT → REVIEWING。 */
    ApplicationVO resubmit(Long id);

    /** 撤回：仅未受理前允许。 */
    ApplicationVO cancel(Long id, String reason);

    /** 审核轨迹（按轮次与时间）。 */
    List<BizReviewRecord> reviewRecords(Long applicationId);
}
'''

FILES['biz/service/impl/ApplicationServiceImpl.java'] = '''package com.yundao.bp.biz.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.biz.constant.ApplicationStatus;
import com.yundao.bp.biz.constant.ReviewResult;
import com.yundao.bp.biz.constant.ReviewStage;
import com.yundao.bp.biz.dto.ApplicationCreateCmd;
import com.yundao.bp.biz.dto.ApplicationVO;
import com.yundao.bp.biz.dto.ReviewCmd;
import com.yundao.bp.biz.entity.BizApplication;
import com.yundao.bp.biz.entity.BizReviewRecord;
import com.yundao.bp.biz.mapper.BizApplicationMapper;
import com.yundao.bp.biz.mapper.BizReviewRecordMapper;
import com.yundao.bp.biz.service.ApplicationService;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 申请与审核实现。
 *
 * <p><b>状态机推进规则</b>：
 * <ul>
 *   <li>提交后 {@code SUBMITTED}，受理后 {@code ACCEPTED→REVIEWING}</li>
 *   <li>审核 {@code PASS}：非终审 → 停留 {@code REVIEWING} 并推进阶段；终审 → {@code APPROVED}</li>
 *   <li>审核 {@code REJECT}：→ {@code REJECTED}（终态）</li>
 *   <li>审核 {@code SUPPLEMENT}：→ {@code SUPPLEMENT}（待补件），补件后 {@code resubmit} 回 {@code REVIEWING}</li>
 * </ul>
 *
 * <p><b>人均收入</b>：{@code incomePerCapita = declaredIncome / familySize}，
 * 用于分档判定（各地政策对照见 {@code 01_需求与功能方案.md} §3.4）。
 */
@Service
public class ApplicationServiceImpl implements ApplicationService {

    private static final Logger log = LoggerFactory.getLogger(ApplicationServiceImpl.class);

    private final BizApplicationMapper appMapper;
    private final BizReviewRecordMapper reviewMapper;
    private final SnowflakeIdGenerator idGen;

    public ApplicationServiceImpl(BizApplicationMapper appMapper,
                                  BizReviewRecordMapper reviewMapper,
                                  SnowflakeIdGenerator idGen) {
        this.appMapper = appMapper;
        this.reviewMapper = reviewMapper;
        this.idGen = idGen;
    }

    // ==================== 创建 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ApplicationVO create(ApplicationCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();

        // 保障房必备：真实性承诺书 + 同意核实
        if (cmd.complianceCommitFlag() == null || cmd.complianceCommitFlag() != 1) {
            throw BizException.paramInvalid("必须签署申报信息真实性承诺书");
        }
        if (cmd.dataShareAgreeFlag() == null || cmd.dataShareAgreeFlag() != 1) {
            throw BizException.paramInvalid("必须书面同意核实申报信息");
        }
        if (cmd.intentAreaMin() != null && cmd.intentAreaMax() != null
                && cmd.intentAreaMin().compareTo(cmd.intentAreaMax()) > 0) {
            throw BizException.paramInvalid("意向最小面积不能大于最大面积");
        }

        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();
        BizApplication e = new BizApplication();
        e.setId(id);
        e.setTenantId(tenantId);
        e.setApplicationNo("BA" + id);
        e.setOrgId(cmd.orgId());
        e.setPersonId(cmd.personId());
        e.setSecurityType(cmd.securityType());
        e.setSecurityMode(blankToNull(cmd.securityMode()) == null ? "HOUSE" : cmd.securityMode());
        e.setApplyChannel(blankToNull(cmd.applyChannel()) == null ? "OFFLINE" : cmd.applyChannel());
        e.setApplyTime(now);
        e.setFamilySize(cmd.familySize());
        e.setIntentDistrict(cmd.intentDistrict());
        e.setIntentProject(cmd.intentProject());
        e.setIntentLayout(cmd.intentLayout());
        e.setIntentAreaMin(cmd.intentAreaMin());
        e.setIntentAreaMax(cmd.intentAreaMax());
        e.setFormData(cmd.formData());
        e.setAttachmentUrls(cmd.attachmentUrls());
        e.setDeclaredIncome(cmd.declaredIncome());
        e.setDeclaredIncomeYear(cmd.declaredIncomeYear());
        e.setFamilyPropertyAmount(cmd.familyPropertyAmount());
        e.setIncomeCheckPeriod(blankToNull(cmd.incomeCheckPeriod()) == null
                ? "LAST_YEAR" : cmd.incomeCheckPeriod());
        // 人均月收入派生
        if (cmd.declaredIncome() != null && cmd.familySize() != null && cmd.familySize() > 0) {
            e.setIncomePerCapita(cmd.declaredIncome()
                    .divide(BigDecimal.valueOf(cmd.familySize()), 2, RoundingMode.HALF_UP));
        }
        e.setComplianceCommitFlag(cmd.complianceCommitFlag());
        e.setDataShareAgreeFlag(cmd.dataShareAgreeFlag());
        e.setRemark(cmd.remark());
        e.setApplicationStatus(ApplicationStatus.SUBMITTED.name());
        e.setCurrentNode(ReviewStage.ACCEPT.name());
        e.setIsDeleted(0);
        e.setCreateTime(now);
        appMapper.insert(e);
        return ApplicationVO.from(e);
    }

    // ==================== 查询 ====================

    @Override
    public ApplicationVO get(Long id) {
        return ApplicationVO.from(require(id));
    }

    @Override
    public PageResult<ApplicationVO> page(long pageNum, long pageSize, String securityType,
                                          String status, Long orgId, String keyword) {
        LambdaQueryWrapper<BizApplication> qw = new LambdaQueryWrapper<BizApplication>()
                .eq(securityType != null && !securityType.isBlank(),
                        BizApplication::getSecurityType, securityType)
                .eq(status != null && !status.isBlank(),
                        BizApplication::getApplicationStatus, status)
                .eq(orgId != null, BizApplication::getOrgId, orgId)
                .orderByDesc(BizApplication::getId);
        if (keyword != null && !keyword.isBlank()) {
            qw.and(w -> w.like(BizApplication::getApplicationNo, keyword));
        }
        IPage<BizApplication> page = appMapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<ApplicationVO> rows = page.getRecords().stream().map(ApplicationVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    public List<BizReviewRecord> reviewRecords(Long applicationId) {
        require(applicationId);
        return reviewMapper.selectList(new LambdaQueryWrapper<BizReviewRecord>()
                .eq(BizReviewRecord::getApplicationId, applicationId)
                .orderByAsc(BizReviewRecord::getReviewRound)
                .orderByAsc(BizReviewRecord::getCreateTime)
                .orderByAsc(BizReviewRecord::getId));
    }

    // ==================== 受理 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ApplicationVO accept(Long id, Long acceptUserId) {
        BizApplication e = require(id);
        transition(e, ApplicationStatus.ACCEPTED);
        e.setAcceptTime(LocalDateTime.now());
        e.setAcceptUserId(acceptUserId);
        // 受理即进入审核中
        e.setApplicationStatus(ApplicationStatus.REVIEWING.name());
        e.setCurrentNode(ReviewStage.FORM.name());
        e.setUpdateTime(LocalDateTime.now());
        appMapper.updateById(e);
        return ApplicationVO.from(e);
    }

    // ==================== 审核 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ApplicationVO review(Long id, ReviewCmd cmd, Long reviewUserId, String reviewUserName) {
        BizApplication e = require(id);
        ApplicationStatus cur = statusOf(e);
        if (!cur.isInReview()) {
            throw BizException.stateConflict(
                    "申请单当前状态（" + cur.label() + "）不可审核");
        }
        // 待补件状态下只能先补件再审核
        if (cur == ApplicationStatus.SUPPLEMENT) {
            throw BizException.stateConflict("申请单待补件，请先补件后重新提交再审核");
        }

        ReviewStage stage;
        try {
            stage = ReviewStage.valueOf(cmd.stage());
        } catch (IllegalArgumentException ex) {
            throw BizException.paramInvalid("审核阶段不合法: " + cmd.stage());
        }
        ReviewResult result;
        try {
            result = ReviewResult.valueOf(cmd.result());
        } catch (IllegalArgumentException ex) {
            throw BizException.paramInvalid("审核结果不合法: " + cmd.result());
        }

        int round = reviewMapper.selectCount(new LambdaQueryWrapper<BizReviewRecord>()
                .eq(BizReviewRecord::getApplicationId, id)).intValue() + 1;

        BizReviewRecord r = new BizReviewRecord();
        r.setId(idGen.nextId());
        r.setTenantId(e.getTenantId());
        r.setApplicationId(id);
        r.setReviewRound(round);
        r.setReviewStage(stage.name());
        r.setReviewDept(blankToNull(cmd.dept()));
        r.setReviewType("MANUAL");
        r.setReviewUserId(reviewUserId);
        r.setReviewUserName(reviewUserName);
        r.setReviewTime(LocalDateTime.now());
        r.setReviewResult(result.name());
        r.setCheckItems(cmd.checkItems());
        r.setReviewOpinion(cmd.opinion());
        r.setCreateTime(LocalDateTime.now());
        reviewMapper.insert(r);

        // 推进状态机
        switch (result) {
            case REJECT -> {
                transition(e, ApplicationStatus.REJECTED);
                e.setRejectReason(cmd.rejectReason() == null
                        ? cmd.opinion() : cmd.rejectReason());
            }
            case SUPPLEMENT -> {
                transition(e, ApplicationStatus.SUPPLEMENT);
                e.setSupplementDemand(cmd.supplementDemand() == null
                        ? cmd.opinion() : cmd.supplementDemand());
            }
            case PASS -> {
                if (stage.isLast()) {
                    transition(e, ApplicationStatus.APPROVED);
                    e.setCurrentNode("DONE");
                } else {
                    // 非终审通过：停留 REVIEWING，推进到下一阶段
                    e.setCurrentNode(stage.next().name());
                }
            }
            default -> {
            }
        }
        e.setUpdateTime(LocalDateTime.now());
        appMapper.updateById(e);
        log.info("申请 {} 审核 {} {} → 状态 {}", e.getApplicationNo(), stage.name(),
                result.name(), e.getApplicationStatus());
        return ApplicationVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ApplicationVO resubmit(Long id) {
        BizApplication e = require(id);
        transition(e, ApplicationStatus.REVIEWING);
        e.setSupplementDemand(null);
        e.setCurrentNode(ReviewStage.FORM.name());
        e.setUpdateTime(LocalDateTime.now());
        appMapper.updateById(e);
        return ApplicationVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ApplicationVO cancel(Long id, String reason) {
        BizApplication e = require(id);
        ApplicationStatus cur = statusOf(e);
        if (cur != ApplicationStatus.DRAFT && cur != ApplicationStatus.SUBMITTED
                && cur != ApplicationStatus.SUPPLEMENT) {
            throw BizException.stateConflict(
                    "当前状态（" + cur.label() + "）不可撤回，已进入审核流程");
        }
        transition(e, ApplicationStatus.CANCELLED);
        e.setRemark(reason == null ? e.getRemark() : reason);
        e.setUpdateTime(LocalDateTime.now());
        appMapper.updateById(e);
        return ApplicationVO.from(e);
    }

    // ==================== 内部 ====================

    private BizApplication require(Long id) {
        BizApplication e = appMapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("申请单");
        }
        return e;
    }

    private static ApplicationStatus statusOf(BizApplication e) {
        try {
            return ApplicationStatus.valueOf(e.getApplicationStatus());
        } catch (IllegalArgumentException ex) {
            throw BizException.stateConflict("申请单状态非法: " + e.getApplicationStatus());
        }
    }

    private static void transition(BizApplication e, ApplicationStatus target) {
        ApplicationStatus from = statusOf(e);
        if (from == target) {
            throw BizException.stateConflict("已处于 " + target.label() + " 状态");
        }
        if (!ApplicationStatus.nextOf(from).contains(target)) {
            throw BizException.stateConflict(
                    "状态不允许从 " + from.label() + " 变更为 " + target.label());
        }
        e.setApplicationStatus(target.name());
    }

    private static String blankToNull(String s) {
        return (s == null || s.isBlank()) ? null : s;
    }
}
'''

FILES['biz/controller/ApplicationController.java'] = '''package com.yundao.bp.biz.controller;

import com.yundao.bp.biz.dto.ApplicationCreateCmd;
import com.yundao.bp.biz.dto.ApplicationVO;
import com.yundao.bp.biz.dto.ReviewCmd;
import com.yundao.bp.biz.entity.BizReviewRecord;
import com.yundao.bp.biz.service.ApplicationService;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 保障房申请与审核接口（BC-05 业务办理）。
 *
 * <p>主干：提交 → 受理 → 审核（多阶段）→ 通过 / 不通过 / 需补件。
 */
@RestController
@RequestMapping("/api/v1/applications")
public class ApplicationController {

    private final ApplicationService applicationService;

    public ApplicationController(ApplicationService applicationService) {
        this.applicationService = applicationService;
    }

    @PostMapping
    public R<ApplicationVO> create(@Valid @RequestBody ApplicationCreateCmd cmd) {
        return R.ok(applicationService.create(cmd));
    }

    @GetMapping("/{id}")
    public R<ApplicationVO> get(@PathVariable Long id) {
        return R.ok(applicationService.get(id));
    }

    @GetMapping
    public R<PageResult<ApplicationVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                             @RequestParam(defaultValue = "20") long pageSize,
                                             @RequestParam(required = false) String securityType,
                                             @RequestParam(required = false) String status,
                                             @RequestParam(required = false) Long orgId,
                                             @RequestParam(required = false) String keyword) {
        return R.ok(applicationService.page(pageNum, pageSize, securityType, status, orgId,
                keyword));
    }

    /** 受理（同时进入审核中）。 */
    @PostMapping("/{id}/accept")
    public R<ApplicationVO> accept(@PathVariable Long id,
                                   @RequestBody(required = false) Cmd cmd) {
        return R.ok(applicationService.accept(id, cmd == null ? null : cmd.userId()));
    }

    /** 提交审核结果。 */
    @PostMapping("/{id}/review")
    public R<ApplicationVO> review(@PathVariable Long id, @Valid @RequestBody ReviewCmd cmd,
                                   @RequestParam(required = false) Long userId,
                                   @RequestParam(required = false) String userName) {
        return R.ok(applicationService.review(id, cmd, userId, userName));
    }

    /** 补件后重新提交。 */
    @PostMapping("/{id}/resubmit")
    public R<ApplicationVO> resubmit(@PathVariable Long id) {
        return R.ok(applicationService.resubmit(id));
    }

    /** 撤回。 */
    @PostMapping("/{id}/cancel")
    public R<ApplicationVO> cancel(@PathVariable Long id,
                                   @RequestBody(required = false) Cmd cmd) {
        return R.ok(applicationService.cancel(id, cmd == null ? null : cmd.reason()));
    }

    /** 审核轨迹。 */
    @GetMapping("/{id}/reviews")
    public R<List<BizReviewRecord>> reviews(@PathVariable Long id) {
        return R.ok(applicationService.reviewRecords(id));
    }

    public record Cmd(Long userId, String reason) {
    }
}
'''

count = 0
for rel, content in FILES.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
    print('  + ' + rel)
print('生成 %d 个文件' % count)
