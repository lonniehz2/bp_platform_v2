package com.yundao.bp.biz.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.biz.constant.ContractStatus;
import com.yundao.bp.biz.constant.AnnualReviewResult;
import com.yundao.bp.biz.constant.ReviewStatus;
import com.yundao.bp.biz.dto.ReviewCreateCmd;
import com.yundao.bp.biz.dto.ReviewFinishCmd;
import com.yundao.bp.biz.dto.ReviewVO;
import com.yundao.bp.biz.entity.BizAnnualReview;
import com.yundao.bp.biz.entity.BizContract;
import com.yundao.bp.biz.mapper.BizAnnualReviewMapper;
import com.yundao.bp.biz.mapper.BizContractMapper;
import com.yundao.bp.biz.dto.TerminationCreateCmd;
import com.yundao.bp.biz.dto.TerminationVO;
import com.yundao.bp.biz.service.AnnualReviewService;
import com.yundao.bp.biz.service.TerminationService;
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
    /** 退租腾退服务（年审结论 EXIT 时自动发起腾退单） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private TerminationService terminationService;

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
        AnnualReviewResult rr;
        try {
            rr = AnnualReviewResult.valueOf(cmd.reviewResult());
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

        // ⭐ 年审结论 EXIT → 自动发起退租腾退单（决策 D25）
        // 否则年审只是"写了句结论"，房源和授权都不会动
        if (rr == AnnualReviewResult.EXIT && e.getContractId() != null) {
            autoCreateTermination(e);
        }

        log.info("复核单 {} 完成：{}（{}）下次复核 {}",
                e.getReviewNo(), rr.label(), e.getReviewYear(), next);
        return ReviewVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public BatchResult createBatch(String reviewYear, Long orgId, String reviewBatch,
                                   boolean dryRun) {
        if (reviewYear == null || !reviewYear.matches("\\d{4}")) {
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

    /**
     * 年审结论 EXIT → 自动发起退租腾退单。
     *
     * <p><b>幂等</b>：该合同已有退租单则跳过，避免重复发起。
     *
     * <p><b>政策</b>：年审退出属政策性退出（非违规），
     * 退租类型用 {@code OTHER}（不能用 EXPEL，否则会误触发 5 年禁申），
     * 并给 3 个月腾退过渡期。
     */
    private void autoCreateTermination(BizAnnualReview rv) {
        if (terminationService == null) {
            log.warn("退租服务不可用，年审 {} 的 EXIT 结论未自动发起腾退单", rv.getReviewNo());
            return;
        }
        try {
            // 幂等：已有退租单则不再发起
            var existing = terminationService.page(1, 1, null, null, rv.getContractId(), null, null);
            if (existing.total() > 0) {
                log.info("合同 {} 已有退租单，年审 {} 不重复发起", rv.getContractId(),
                        rv.getReviewNo());
                return;
            }
            LocalDate planExit = LocalDate.now().plusMonths(3);
            String reason = "年审复核不再符合保障条件（复核单 " + rv.getReviewNo() + "）"
                    + (rv.getAdjustContent() == null ? "" : "：" + rv.getAdjustContent());
            TerminationVO t = terminationService.apply(new TerminationCreateCmd(
                    rv.getContractId(), rv.getHouseId(), rv.getPersonId(),
                    "OTHER", planExit, reason,
                    3, new java.math.BigDecimal("1.5"), null));

            // 回写年审单，便于追溯
            String old = rv.getAdjustContent() == null ? "" : rv.getAdjustContent();
            rv.setAdjustContent(old + "｜已自动发起退租单 " + t.terminationNo());
            rv.setUpdateTime(LocalDateTime.now());
            mapper.updateById(rv);
            log.info("⭐⭐ 年审 {} 结论 EXIT → 已自动发起退租单 {}（计划退房 {}）",
                    rv.getReviewNo(), t.terminationNo(), planExit);
        } catch (Exception ex) {
            // 自动发起失败不能回滚年审结论（结论本身是有效的），仅记录待人工处理
            log.error("年审 {} 自动发起退租单失败，需人工处理：{}", rv.getReviewNo(),
                    ex.getMessage());
        }
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
