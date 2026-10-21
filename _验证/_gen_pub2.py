# -*- coding: utf-8 -*-
"""生成 公示 + 年审（服务 + 控制器）"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['biz/service/PublicityService.java'] = '''package com.yundao.bp.biz.service;

import com.yundao.bp.biz.dto.PublicityCreateCmd;
import com.yundao.bp.biz.dto.PublicityVO;
import com.yundao.bp.common.api.PageResult;
import java.time.LocalDate;

/**
 * 公示服务。
 *
 * <p>⭐ <b>合规（决策 D23）</b>：
 * <ul>
 *   <li>配租公示（ALLOCATION）公示期<b>不得少于 7 个自然日</b></li>
 *   <li>配租公示<b>未结束不得签约</b>（保证异议期）</li>
 *   <li>公示结束才能推进到下一环节</li>
 * </ul>
 */
public interface PublicityService {

    /** 创建公示（配租公示校验 7 天公示期）。 */
    PublicityVO create(PublicityCreateCmd cmd);

    PublicityVO get(Long id);

    PageResult<PublicityVO> page(long pageNum, long pageSize, String type, Long orgId,
                                 String status);

    /** 发布公示（草稿 → 已发布）。 */
    PublicityVO publish(Long id);

    /** 结束公示（已发布 → 已结束）。 */
    PublicityVO close(Long id, String remark);

    /**
     * 校验某组织/类型是否已完成合规公示。
     *
     * <p>供签约前置校验调用：返回 true 表示存在已结束的配租公示。
     */
    boolean hasCompletedAllocationPublicity(Long orgId, LocalDate referenceDate);
}
'''

FILES['biz/service/impl/PublicityServiceImpl.java'] = '''package com.yundao.bp.biz.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.biz.constant.PublicityStatus;
import com.yundao.bp.biz.constant.PublicityType;
import com.yundao.bp.biz.dto.PublicityCreateCmd;
import com.yundao.bp.biz.dto.PublicityVO;
import com.yundao.bp.biz.entity.BizPublicity;
import com.yundao.bp.biz.mapper.BizPublicityMapper;
import com.yundao.bp.biz.service.PublicityService;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 公示实现。
 *
 * <p><b>合规规则</b>：配租公示至少 7 个自然日；公示未结束不得签约。
 */
@Service
public class PublicityServiceImpl implements PublicityService {

    private static final Logger log = LoggerFactory.getLogger(PublicityServiceImpl.class);

    /** 配租公示最短公示期（自然日） */
    private static final int MIN_ALLOCATION_DAYS = 7;

    private final BizPublicityMapper mapper;
    private final SnowflakeIdGenerator idGen;

    public PublicityServiceImpl(BizPublicityMapper mapper, SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public PublicityVO create(PublicityCreateCmd cmd) {
        if (cmd.endDate().isBefore(cmd.startDate())) {
            throw BizException.paramInvalid("公示结束日期不能早于开始日期");
        }
        PublicityType tp;
        try {
            tp = PublicityType.valueOf(cmd.publicityType());
        } catch (IllegalArgumentException e) {
            throw BizException.paramInvalid("公示类型不合法: " + cmd.publicityType());
        }
        long days = ChronoUnit.DAYS.between(cmd.startDate(), cmd.endDate()) + 1;
        // 配租公示必须满 7 个自然日（含首尾）
        if (tp == PublicityType.ALLOCATION && days < MIN_ALLOCATION_DAYS) {
            throw BizException.paramInvalid(
                    "配租公示期不得少于 " + MIN_ALLOCATION_DAYS + " 个自然日，当前仅 "
                            + days + " 天（" + cmd.startDate() + " ~ " + cmd.endDate() + "）");
        }

        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();
        BizPublicity e = new BizPublicity();
        e.setId(id);
        e.setTenantId(TenantContext.tenantId());
        e.setPublicityNo("PB" + id);
        e.setPublicityType(tp.name());
        e.setOrgId(cmd.orgId());
        e.setTitle(cmd.title());
        e.setContent(cmd.content());
        e.setStartDate(cmd.startDate());
        e.setEndDate(cmd.endDate());
        e.setAttachmentUrl(cmd.attachmentUrl());
        e.setPublicityStatus(PublicityStatus.DRAFT.name());
        e.setCreateTime(now);
        e.setUpdateTime(now);
        mapper.insert(e);
        log.info("公示创建 {}：{} {}~{}（{} 天）", e.getPublicityNo(), tp.label(),
                cmd.startDate(), cmd.endDate(), days);
        return PublicityVO.from(e);
    }

    @Override
    public PublicityVO get(Long id) {
        return PublicityVO.from(require(id));
    }

    @Override
    public PageResult<PublicityVO> page(long pageNum, long pageSize, String type, Long orgId,
                                        String status) {
        LambdaQueryWrapper<BizPublicity> qw = new LambdaQueryWrapper<BizPublicity>()
                .eq(type != null && !type.isBlank(), BizPublicity::getPublicityType, type)
                .eq(orgId != null, BizPublicity::getOrgId, orgId)
                .eq(status != null && !status.isBlank(), BizPublicity::getPublicityStatus, status)
                .orderByDesc(BizPublicity::getId);
        IPage<BizPublicity> page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<PublicityVO> rows = page.getRecords().stream().map(PublicityVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public PublicityVO publish(Long id) {
        BizPublicity e = require(id);
        transition(e, PublicityStatus.PUBLISHED);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return PublicityVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public PublicityVO close(Long id, String remark) {
        BizPublicity e = require(id);
        transition(e, PublicityStatus.CLOSED);
        // 提前结束配租公示视为不合规，记录警告（仍允许关闭，由人工判断特殊情况）
        if (PublicityType.ALLOCATION.name().equals(e.getPublicityType())
                && e.getEndDate() != null && LocalDate.now().isBefore(e.getEndDate())) {
            log.warn("⚠️ 配租公示 {} 提前结束（应公示至 {}），请确认是否合规",
                    e.getPublicityNo(), e.getEndDate());
        }
        if (remark != null && !remark.isBlank()) {
            e.setContent((e.getContent() == null ? "" : e.getContent() + "\\n") + remark);
        }
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return PublicityVO.from(e);
    }

    @Override
    public boolean hasCompletedAllocationPublicity(Long orgId, LocalDate referenceDate) {
        Long n = mapper.selectCount(new LambdaQueryWrapper<BizPublicity>()
                .eq(BizPublicity::getPublicityType, PublicityType.ALLOCATION.name())
                .eq(BizPublicity::getPublicityStatus, PublicityStatus.CLOSED.name())
                .eq(orgId != null, BizPublicity::getOrgId, orgId));
        return n != null && n > 0;
    }

    // ==================== 内部 ====================

    private BizPublicity require(Long id) {
        BizPublicity e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("公示");
        }
        return e;
    }

    private static void transition(BizPublicity e, PublicityStatus target) {
        PublicityStatus from;
        try {
            from = PublicityStatus.valueOf(e.getPublicityStatus());
        } catch (IllegalArgumentException ex) {
            throw BizException.stateConflict("公示状态非法: " + e.getPublicityStatus());
        }
        if (from == target) {
            throw BizException.stateConflict("已处于 " + target.label() + " 状态");
        }
        if (!PublicityStatus.nextOf(from).contains(target)) {
            throw BizException.stateConflict(
                    "公示状态不允许从 " + from.label() + " 变更为 " + target.label());
        }
        e.setPublicityStatus(target.name());
    }
}
'''

FILES['biz/service/AnnualReviewService.java'] = '''package com.yundao.bp.biz.service;

import com.yundao.bp.biz.dto.ReviewCreateCmd;
import com.yundao.bp.biz.dto.ReviewFinishCmd;
import com.yundao.bp.biz.dto.ReviewVO;
import com.yundao.bp.common.api.PageResult;
import java.util.List;

/**
 * 年审（复核）服务。
 *
 * <p><b>业务意义</b>：保障房要求保障对象每年复核收入/房产/人口变化，
 * 结果决定「保留 / 调租 / 退出」，是防止"骗保""超标占用"的核心手段。
 */
public interface AnnualReviewService {

    /** 创建复核单（幂等：同人同年度同类型仅一条）。 */
    ReviewVO create(ReviewCreateCmd cmd);

    ReviewVO get(Long id);

    PageResult<ReviewVO> page(long pageNum, long pageSize, Long personId, String reviewYear,
                              String reviewType, String status);

    /** 开始复核（待复核 → 复核中）。 */
    ReviewVO start(Long id);

    /** 完成复核（填写结果，自动推算下次复核日期）。 */
    ReviewVO finish(Long id, ReviewFinishCmd cmd);

    /**
     * 批量生成年度复核单。
     *
     * <p>扫描生效合同，为该年度未创建复核单的合同生成复核单。
     */
    BatchResult createBatch(String reviewYear, Long orgId, String reviewBatch, boolean dryRun);

    /** 将超期未完成的复核置为 OVERDUE，返回处理数。 */
    int markOverdue();

    /** 批量结果。 */
    record BatchResult(String reviewYear, int scanned, int created, int skipped,
                       boolean dryRun, List<String> skipReasons) {
    }
}
'''

FILES['biz/service/impl/AnnualReviewServiceImpl.java'] = '''package com.yundao.bp.biz.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.biz.constant.ContractStatus;
import com.yundao.bp.biz.constant.ReviewResult;
import com.yundao.bp.biz.constant.ReviewStatus;
import com.yundao.bp.biz.dto.ReviewCreateCmd;
import com.yundao.bp.biz.dto.ReviewFinishCmd;
import com.yundao.bp.biz.dto.ReviewVO;
import com.yundao.bp.biz.entity.BizAnnualReview;
import com.yundao.bp.biz.entity.BizContract;
import com.yundao.bp.biz.mapper.BizAnnualReviewMapper;
import com.yundao.bp.biz.mapper.BizContractMapper;
import com.yundao.bp.biz.service.AnnualReviewService;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 年审（复核）实现。
 */
@Service
public class AnnualReviewServiceImpl implements AnnualReviewService {

    private static final Logger log = LoggerFactory.getLogger(AnnualReviewServiceImpl.class);

    private final BizAnnualReviewMapper mapper;
    private final BizContractMapper contractMapper;
    private final SnowflakeIdGenerator idGen;

    public AnnualReviewServiceImpl(BizAnnualReviewMapper mapper,
                                   BizContractMapper contractMapper,
                                   SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.contractMapper = contractMapper;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ReviewVO create(ReviewCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();
        // 幂等：同人 + 同年度 + 同类型
        Long dup = mapper.selectCount(new LambdaQueryWrapper<BizAnnualReview>()
                .eq(BizAnnualReview::getPersonId, cmd.personId())
                .eq(BizAnnualReview::getReviewYear, cmd.reviewYear())
                .eq(BizAnnualReview::getReviewType, cmd.reviewType()));
        if (dup != null && dup > 0) {
            throw BizException.stateConflict(
                    "该人员 " + cmd.reviewYear() + " 年度已有" + cmd.reviewType() + "复核单");
        }
        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();
        BizAnnualReview e = new BizAnnualReview();
        e.setId(id);
        e.setTenantId(tenantId);
        e.setReviewNo("AR" + id);
        e.setPersonId(cmd.personId());
        e.setContractId(cmd.contractId());
        e.setHouseId(cmd.houseId());
        e.setReviewYear(cmd.reviewYear());
        e.setReviewBatch(cmd.reviewBatch());
        e.setReviewType(cmd.reviewType());
        e.setTriggerReason(cmd.triggerReason());
        e.setReviewStatus(ReviewStatus.PENDING.name());
        e.setCreateTime(now);
        e.setUpdateTime(now);
        mapper.insert(e);
        return ReviewVO.from(e);
    }

    @Override
    public ReviewVO get(Long id) {
        return ReviewVO.from(require(id));
    }

    @Override
    public PageResult<ReviewVO> page(long pageNum, long pageSize, Long personId,
                                     String reviewYear, String reviewType, String status) {
        LambdaQueryWrapper<BizAnnualReview> qw = new LambdaQueryWrapper<BizAnnualReview>()
                .eq(personId != null, BizAnnualReview::getPersonId, personId)
                .eq(reviewYear != null && !reviewYear.isBlank(),
                        BizAnnualReview::getReviewYear, reviewYear)
                .eq(reviewType != null && !reviewType.isBlank(),
                        BizAnnualReview::getReviewType, reviewType)
                .eq(status != null && !status.isBlank(), BizAnnualReview::getReviewStatus, status)
                .orderByDesc(BizAnnualReview::getId);
        IPage<BizAnnualReview> page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<ReviewVO> rows = page.getRecords().stream().map(ReviewVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ReviewVO start(Long id) {
        BizAnnualReview e = require(id);
        transition(e, ReviewStatus.REVIEWING);
        e.setReviewDate(LocalDate.now());
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return ReviewVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ReviewVO finish(Long id, ReviewFinishCmd cmd) {
        BizAnnualReview e = require(id);
        ReviewStatus from = statusOf(e);
        if (from.isTerminal()) {
            throw BizException.stateConflict("复核已" + from.label());
        }
        ReviewResult rr;
        try {
            rr = ReviewResult.valueOf(cmd.reviewResult());
        } catch (IllegalArgumentException ex) {
            throw BizException.paramInvalid("复核结果不合法: " + cmd.reviewResult());
        }
        // 结果 ADJUST/EXIT 必须说明处置内容，便于后续执行
        if (rr.needsAction()
                && (cmd.adjustContent() == null || cmd.adjustContent().isBlank())) {
            throw BizException.paramInvalid(
                    "复核结果为「" + rr.label() + "」时必须填写调整/处置内容");
        }

        e.setReviewResult(rr.name());
        e.setCheckResult(cmd.checkResult());
        e.setAdjustContent(cmd.adjustContent());
        e.setReviewUserId(cmd.reviewUserId());
        e.setReviewStatus(ReviewStatus.DONE.name());
        e.setReviewDate(LocalDate.now());
        // 下次复核日期：默认次年同日
        LocalDate next = cmd.nextReviewDate() == null || cmd.nextReviewDate().isBlank()
                ? LocalDate.now().plusYears(1) : LocalDate.parse(cmd.nextReviewDate());
        e.setNextReviewDate(next);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);

        log.info("复核单 {} 完成：{}（{}）下次复核 {}",
                e.getReviewNo(), rr.label(), e.getReviewYear(), next);
        return ReviewVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public BatchResult createBatch(String reviewYear, Long orgId, String reviewBatch,
                                   boolean dryRun) {
        if (reviewYear == null || !reviewYear.matches("\\\\d{4}")) {
            throw BizException.paramInvalid("复核年度格式应为 YYYY");
        }
        List<BizContract> contracts = contractMapper.selectList(
                new LambdaQueryWrapper<BizContract>()
                        .in(BizContract::getContractStatus, List.of(
                                ContractStatus.EFFECTIVE.name(),
                                ContractStatus.RENEWING.name()))
                        .eq(orgId != null, BizContract::getOrgId, orgId)
                        .orderByAsc(BizContract::getId));

        int created = 0;
        int skipped = 0;
        List<String> skipReasons = new ArrayList<>();
        for (BizContract ct : contracts) {
            Long dup = mapper.selectCount(new LambdaQueryWrapper<BizAnnualReview>()
                    .eq(BizAnnualReview::getPersonId, ct.getLesseePersonId())
                    .eq(BizAnnualReview::getReviewYear, reviewYear)
                    .eq(BizAnnualReview::getReviewType, "ANNUAL"));
            if (dup != null && dup > 0) {
                skipped++;
                skipReasons.add("合同 " + ct.getContractNo() + "：该年度复核单已存在");
                continue;
            }
            if (!dryRun) {
                long id = idGen.nextId();
                LocalDateTime now = LocalDateTime.now();
                BizAnnualReview e = new BizAnnualReview();
                e.setId(id);
                e.setTenantId(TenantContext.tenantId());
                e.setReviewNo("AR" + id);
                e.setPersonId(ct.getLesseePersonId());
                e.setContractId(ct.getId());
                e.setHouseId(ct.getHouseId());
                e.setReviewYear(reviewYear);
                e.setReviewBatch(reviewBatch);
                e.setReviewType("ANNUAL");
                e.setTriggerReason("年度例行复核");
                e.setReviewStatus(ReviewStatus.PENDING.name());
                e.setCreateTime(now);
                e.setUpdateTime(now);
                mapper.insert(e);
            }
            created++;
        }
        log.info("年审批量生成[{}]：年度 {} 扫描 {} 生成 {} 跳过 {}",
                dryRun ? "试运行" : "已落库", reviewYear, contracts.size(), created, skipped);
        return new BatchResult(reviewYear, contracts.size(), created, skipped, dryRun,
                skipReasons);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int markOverdue() {
        // 超过当年 12-31 仍未完成的年度复核置为逾期
        String thisYear = String.valueOf(LocalDate.now().getYear());
        List<BizAnnualReview> list = mapper.selectList(
                new LambdaQueryWrapper<BizAnnualReview>()
                        .in(BizAnnualReview::getReviewStatus, List.of(
                                ReviewStatus.PENDING.name(), ReviewStatus.REVIEWING.name()))
                        .lt(BizAnnualReview::getReviewYear, thisYear));
        int n = 0;
        for (BizAnnualReview e : list) {
            e.setReviewStatus(ReviewStatus.OVERDUE.name());
            e.setUpdateTime(LocalDateTime.now());
            mapper.updateById(e);
            n++;
        }
        if (n > 0) {
            log.warn("年审逾期标记 {} 条", n);
        }
        return n;
    }

    // ==================== 内部 ====================

    private BizAnnualReview require(Long id) {
        BizAnnualReview e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("复核单");
        }
        return e;
    }

    private static ReviewStatus statusOf(BizAnnualReview e) {
        try {
            return ReviewStatus.valueOf(e.getReviewStatus());
        } catch (IllegalArgumentException ex) {
            throw BizException.stateConflict("复核状态非法: " + e.getReviewStatus());
        }
    }

    private static void transition(BizAnnualReview e, ReviewStatus target) {
        ReviewStatus from = statusOf(e);
        if (from == target) {
            throw BizException.stateConflict("已处于 " + target.label() + " 状态");
        }
        if (!ReviewStatus.nextOf(from).contains(target)) {
            throw BizException.stateConflict(
                    "复核状态不允许从 " + from.label() + " 变更为 " + target.label());
        }
        e.setReviewStatus(target.name());
    }
}
'''

FILES['biz/controller/PublicityReviewController.java'] = '''package com.yundao.bp.biz.controller;

import com.yundao.bp.biz.dto.PublicityCreateCmd;
import com.yundao.bp.biz.dto.PublicityVO;
import com.yundao.bp.biz.dto.ReviewCreateCmd;
import com.yundao.bp.biz.dto.ReviewFinishCmd;
import com.yundao.bp.biz.dto.ReviewVO;
import com.yundao.bp.biz.service.AnnualReviewService;
import com.yundao.bp.biz.service.PublicityService;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import jakarta.validation.Valid;
import java.time.LocalDate;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 公示与年审接口（BC-05）。
 *
 * <p>⭐ 配租结果必须公示（≥7 个自然日）才能推进签约。
 */
@RestController
@RequestMapping("/api/v1")
public class PublicityReviewController {

    private final PublicityService publicityService;
    private final AnnualReviewService reviewService;

    public PublicityReviewController(PublicityService publicityService,
                                     AnnualReviewService reviewService) {
        this.publicityService = publicityService;
        this.reviewService = reviewService;
    }

    // ---------- 公示 ----------

    @PostMapping("/publicities")
    public R<PublicityVO> createPublicity(@Valid @RequestBody PublicityCreateCmd cmd) {
        return R.ok(publicityService.create(cmd));
    }

    @GetMapping("/publicities/{id}")
    public R<PublicityVO> getPublicity(@PathVariable Long id) {
        return R.ok(publicityService.get(id));
    }

    @GetMapping("/publicities")
    public R<PageResult<PublicityVO>> pagePublicity(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) String type,
            @RequestParam(required = false) Long orgId,
            @RequestParam(required = false) String status) {
        return R.ok(publicityService.page(pageNum, pageSize, type, orgId, status));
    }

    @PostMapping("/publicities/{id}/publish")
    public R<PublicityVO> publishPublicity(@PathVariable Long id) {
        return R.ok(publicityService.publish(id));
    }

    @PostMapping("/publicities/{id}/close")
    public R<PublicityVO> closePublicity(@PathVariable Long id,
                                         @RequestBody(required = false) RemarkCmd cmd) {
        return R.ok(publicityService.close(id, cmd == null ? null : cmd.remark()));
    }

    /** 是否已完成配租公示（签约前置校验）。 */
    @GetMapping("/publicities/allocation-check")
    public R<Boolean> allocationCheck(
            @RequestParam(required = false) Long orgId,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate referenceDate) {
        return R.ok(publicityService.hasCompletedAllocationPublicity(orgId, referenceDate));
    }

    // ---------- 年审 ----------

    @PostMapping("/annual-reviews")
    public R<ReviewVO> createReview(@Valid @RequestBody ReviewCreateCmd cmd) {
        return R.ok(reviewService.create(cmd));
    }

    @GetMapping("/annual-reviews/{id}")
    public R<ReviewVO> getReview(@PathVariable Long id) {
        return R.ok(reviewService.get(id));
    }

    @GetMapping("/annual-reviews")
    public R<PageResult<ReviewVO>> pageReview(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) Long personId,
            @RequestParam(required = false) String reviewYear,
            @RequestParam(required = false) String reviewType,
            @RequestParam(required = false) String status) {
        return R.ok(reviewService.page(pageNum, pageSize, personId, reviewYear, reviewType,
                status));
    }

    @PostMapping("/annual-reviews/{id}/start")
    public R<ReviewVO> startReview(@PathVariable Long id) {
        return R.ok(reviewService.start(id));
    }

    /** 完成复核。 */
    @PostMapping("/annual-reviews/{id}/finish")
    public R<ReviewVO> finishReview(@PathVariable Long id,
                                    @Valid @RequestBody ReviewFinishCmd cmd) {
        return R.ok(reviewService.finish(id, cmd));
    }

    /** 批量生成年度复核单。 */
    @PostMapping("/annual-reviews/batch")
    public R<AnnualReviewService.BatchResult> createReviewBatch(@RequestBody BatchReviewCmd cmd) {
        return R.ok(reviewService.createBatch(cmd.reviewYear(), cmd.orgId(), cmd.reviewBatch(),
                cmd.dryRun() != null && cmd.dryRun()));
    }

    /** 标记逾期未复核。 */
    @PostMapping("/annual-reviews/mark-overdue")
    public R<Integer> markOverdue() {
        return R.ok(reviewService.markOverdue());
    }

    public record RemarkCmd(String remark) {
    }

    public record BatchReviewCmd(String reviewYear, Long orgId, String reviewBatch,
                                 Boolean dryRun) {
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
