package com.yundao.bp.biz.controller;

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
