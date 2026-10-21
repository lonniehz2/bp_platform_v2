package com.yundao.bp.biz.controller;

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
