package com.yundao.bp.biz.controller;

import com.yundao.bp.biz.dto.ChangeCreateCmd;
import com.yundao.bp.biz.dto.ChangeVO;
import com.yundao.bp.biz.service.ContractChangeService;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import jakarta.validation.Valid;
import java.math.BigDecimal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 合同变更接口（BC-05）。
 *
 * <p>⭐ 年审结论「调整租金」通过本接口落地到合同，否则年审只是一段文字。
 */
@RestController
@RequestMapping("/api/v1")
public class ContractChangeController {

    private final ContractChangeService service;

    public ContractChangeController(ContractChangeService service) {
        this.service = service;
    }

    /** 发起变更（合同维度）。 */
    @PostMapping("/contracts/{contractId}/changes")
    public R<ChangeVO> create(@PathVariable Long contractId,
                              @Valid @RequestBody ChangeCreateCmd cmd) {
        return R.ok(service.create(contractId, cmd));
    }

    /** 由年审结论发起调租。 */
    @PostMapping("/annual-reviews/{reviewId}/rent-change")
    public R<ChangeVO> fromReview(@PathVariable Long reviewId, @RequestBody FromReviewCmd cmd) {
        return R.ok(service.createFromReview(reviewId, cmd.newMonthlyRent(), cmd.reason()));
    }

    @GetMapping("/contract-changes/{id}")
    public R<ChangeVO> get(@PathVariable Long id) {
        return R.ok(service.get(id));
    }

    @GetMapping("/contract-changes")
    public R<PageResult<ChangeVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                        @RequestParam(defaultValue = "20") long pageSize,
                                        @RequestParam(required = false) Long contractId,
                                        @RequestParam(required = false) String changeType,
                                        @RequestParam(required = false) String status) {
        return R.ok(service.page(pageNum, pageSize, contractId, changeType, status));
    }

    /** 批准并写回合同。 */
    @PostMapping("/contract-changes/{id}/approve")
    public R<ChangeVO> approve(@PathVariable Long id) {
        return R.ok(service.approve(id));
    }

    @PostMapping("/contract-changes/{id}/reject")
    public R<ChangeVO> reject(@PathVariable Long id,
                              @RequestBody(required = false) ReasonCmd cmd) {
        return R.ok(service.reject(id, cmd == null ? null : cmd.reason()));
    }

    public record FromReviewCmd(BigDecimal newMonthlyRent, String reason) {
    }

    public record ReasonCmd(String reason) {
    }
}
