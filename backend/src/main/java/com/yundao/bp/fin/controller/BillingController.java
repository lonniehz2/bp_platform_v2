package com.yundao.bp.fin.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.fin.dto.BillCreateCmd;
import com.yundao.bp.fin.dto.BillVO;
import com.yundao.bp.fin.dto.PaymentCreateCmd;
import com.yundao.bp.fin.dto.PaymentVO;
import com.yundao.bp.fin.service.BillingService;
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
 * 账单与收款接口（BC-08 资金账务）。
 */
@RestController
@RequestMapping("/api/v1/fin")
public class BillingController {

    private final BillingService billingService;

    public BillingController(BillingService billingService) {
        this.billingService = billingService;
    }

    // ---------- 账单 ----------

    @com.yundao.bp.iam.security.RequirePerm("fin:bill:create")
    @PostMapping("/bills")
    public R<BillVO> createBill(@Valid @RequestBody BillCreateCmd cmd) {
        return R.ok(billingService.createBill(cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:bill:view")
    @GetMapping("/bills/{id}")
    public R<BillVO> getBill(@PathVariable Long id) {
        return R.ok(billingService.getBill(id));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:bill:view")
    @GetMapping("/bills")
    public R<PageResult<BillVO>> pageBills(@RequestParam(defaultValue = "1") long pageNum,
                                           @RequestParam(defaultValue = "20") long pageSize,
                                           @RequestParam(required = false) Long orgId,
                                           @RequestParam(required = false) Long contractId,
                                           @RequestParam(required = false) Long personId,
                                           @RequestParam(required = false) String status,
                                           @RequestParam(required = false) String keyword) {
        return R.ok(billingService.pageBills(pageNum, pageSize, orgId, contractId, personId,
                status, keyword));
    }

    /** 逾期扫描。 */
    @com.yundao.bp.iam.security.RequirePerm("fin:bill:scan")
    @PostMapping("/bills/scan-overdue")
    public R<Integer> scanOverdue() {
        return R.ok(billingService.scanOverdue());
    }

    /** 减免。 */
    @com.yundao.bp.iam.security.RequirePerm("fin:bill:create")
    @PostMapping("/bills/{id}/waive")
    public R<BillVO> waive(@PathVariable Long id, @RequestBody WaiveCmd cmd) {
        return R.ok(billingService.waiveBill(id, cmd.waiveAmount(), cmd.reason()));
    }

    /** 作废。 */
    @com.yundao.bp.iam.security.RequirePerm("fin:bill:cancel")
    @PostMapping("/bills/{id}/cancel")
    public R<BillVO> cancel(@PathVariable Long id, @RequestBody(required = false) ReasonCmd cmd) {
        return R.ok(billingService.cancelBill(id, cmd == null ? null : cmd.reason()));
    }

    // ---------- 收款 ----------

    @com.yundao.bp.iam.security.RequirePerm("fin:payment:pay")
    @PostMapping("/payments")
    public R<PaymentVO> createPayment(@Valid @RequestBody PaymentCreateCmd cmd) {
        return R.ok(billingService.createPayment(cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:payment:pay")
    @GetMapping("/payments/{id}")
    public R<PaymentVO> getPayment(@PathVariable Long id) {
        return R.ok(billingService.getPayment(id));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:payment:pay")
    @GetMapping("/payments")
    public R<PageResult<PaymentVO>> pagePayments(@RequestParam(defaultValue = "1") long pageNum,
                                                 @RequestParam(defaultValue = "20") long pageSize,
                                                 @RequestParam(required = false) Long orgId,
                                                 @RequestParam(required = false) Long personId,
                                                 @RequestParam(required = false) String status,
                                                 @RequestParam(required = false) String keyword) {
        return R.ok(billingService.pagePayments(pageNum, pageSize, orgId, personId, status,
                keyword));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:payment:pay")
    @PostMapping("/payments/{id}/confirm")
    public R<PaymentVO> confirm(@PathVariable Long id) {
        return R.ok(billingService.confirmPayment(id));
    }

    /** 核销：把收款单的钱核到账单上。 */
    @com.yundao.bp.iam.security.RequirePerm("fin:payment:pay")
    @PostMapping("/payments/{paymentId}/allocate")
    public R<BillVO> allocate(@PathVariable Long paymentId, @RequestBody AllocateCmd cmd) {
        return R.ok(billingService.allocate(paymentId, cmd.billId(), cmd.amount()));
    }

    public record WaiveCmd(BigDecimal waiveAmount, String reason) {
    }

    public record ReasonCmd(String reason) {
    }

    public record AllocateCmd(Long billId, BigDecimal amount) {
    }
}
