package com.yundao.bp.fin.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.fin.dto.DepositCreateCmd;
import com.yundao.bp.fin.dto.DepositVO;
import com.yundao.bp.fin.dto.RefundCreateCmd;
import com.yundao.bp.fin.dto.RefundVO;
import com.yundao.bp.fin.service.DepositRefundService;
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
 * 押金台账与退款接口（BC-08 资金账务）。
 *
 * <p>退租结算落地：押金抵扣 → 申请退款 → 审批 → 打款（自动扣减台账余额）。
 */
@RestController
@RequestMapping("/api/v1/fin")
public class DepositRefundController {

    private final DepositRefundService service;

    public DepositRefundController(DepositRefundService service) {
        this.service = service;
    }

    // ---------- 押金 ----------

    @PostMapping("/deposits")
    public R<DepositVO> createDeposit(@Valid @RequestBody DepositCreateCmd cmd) {
        return R.ok(service.createDeposit(cmd));
    }

    @GetMapping("/deposits/{id}")
    public R<DepositVO> getDeposit(@PathVariable Long id) {
        return R.ok(service.getDeposit(id));
    }

    @GetMapping("/deposits/by-contract/{contractId}")
    public R<DepositVO> byContract(@PathVariable Long contractId) {
        return R.ok(service.getDepositByContract(contractId));
    }

    @GetMapping("/deposits")
    public R<PageResult<DepositVO>> pageDeposits(@RequestParam(defaultValue = "1") long pageNum,
                                                 @RequestParam(defaultValue = "20") long pageSize,
                                                 @RequestParam(required = false) Long contractId,
                                                 @RequestParam(required = false) Long personId,
                                                 @RequestParam(required = false) String status) {
        return R.ok(service.pageDeposits(pageNum, pageSize, contractId, personId, status));
    }

    @PostMapping("/deposits/{id}/receive")
    public R<DepositVO> receive(@PathVariable Long id, @RequestBody AmountCmd cmd) {
        return R.ok(service.receiveDeposit(id, cmd.amount()));
    }

    /** 押金抵扣（退租损坏赔偿等）。 */
    @PostMapping("/deposits/{id}/deduct")
    public R<DepositVO> deduct(@PathVariable Long id, @RequestBody AmountCmd cmd) {
        return R.ok(service.deductDeposit(id, cmd.amount(), cmd.reason()));
    }

    // ---------- 退款 ----------

    @PostMapping("/refunds")
    public R<RefundVO> createRefund(@Valid @RequestBody RefundCreateCmd cmd) {
        return R.ok(service.createRefund(cmd));
    }

    @GetMapping("/refunds/{id}")
    public R<RefundVO> getRefund(@PathVariable Long id) {
        return R.ok(service.getRefund(id));
    }

    @GetMapping("/refunds")
    public R<PageResult<RefundVO>> pageRefunds(@RequestParam(defaultValue = "1") long pageNum,
                                               @RequestParam(defaultValue = "20") long pageSize,
                                               @RequestParam(required = false) Long personId,
                                               @RequestParam(required = false) Long contractId,
                                               @RequestParam(required = false) String status) {
        return R.ok(service.pageRefunds(pageNum, pageSize, personId, contractId, status));
    }

    @PostMapping("/refunds/{id}/approve")
    public R<RefundVO> approve(@PathVariable Long id, @RequestBody(required = false) ApproveCmd cmd) {
        return R.ok(service.approveRefund(id, cmd == null ? null : cmd.approveById()));
    }

    @PostMapping("/refunds/{id}/reject")
    public R<RefundVO> reject(@PathVariable Long id, @RequestBody(required = false) ApproveCmd cmd) {
        return R.ok(service.rejectRefund(id,
                cmd == null ? null : cmd.approveById(),
                cmd == null ? null : cmd.reason()));
    }

    /** 打款完成（联动押金台账）。 */
    @PostMapping("/refunds/{id}/complete")
    public R<RefundVO> complete(@PathVariable Long id) {
        return R.ok(service.completeRefund(id));
    }

    public record AmountCmd(BigDecimal amount, String reason) {
    }

    public record ApproveCmd(Long approveById, String reason) {
    }
}
