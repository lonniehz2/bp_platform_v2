package com.yundao.bp.fin.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.fin.dto.BillCreateCmd;
import com.yundao.bp.fin.dto.BillVO;
import com.yundao.bp.fin.dto.PaymentCreateCmd;
import com.yundao.bp.fin.dto.PaymentVO;
import com.yundao.bp.iam.security.RequirePerm;
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

    /**
     * 公摊费用分摊出账（物业管理场景）。
     *
     * <p>把公共区域总费用按建筑面积或户数分摊到在租房源，为每套生成一张账单。
     */
    @PostMapping("/bills/generate-shared")
    @RequirePerm("fin:bill:create")
    public R<java.util.Map<String, Object>> generateShared(
            @Valid @RequestBody com.yundao.bp.fin.dto.SharedBillCmd cmd) {
        return R.ok(billingService.generateSharedBills(cmd));
    }

    @PostMapping("/bills")
    @RequirePerm("fin:bill:create")
    public R<BillVO> createBill(@Valid @RequestBody BillCreateCmd cmd) {
        return R.ok(billingService.createBill(cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:fin:view")
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
                                           @RequestParam(required = false) Long houseId,
                                           @RequestParam(required = false) String status,
                                           @RequestParam(required = false) String keyword) {
        return R.ok(billingService.pageBills(pageNum, pageSize, orgId, contractId, personId, houseId,
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

    /**
     * 账单趋势：近 N 个月的应收 / 实收 / 收缴率。
     *
     * <p>按账单所属账期（billPeriod，形如 2026-10）统计；
     * 实收取 paidAmount 合计，收缴率 = 实收 / 应收。
     */
    @com.yundao.bp.iam.security.RequirePerm("fin:bill:view")
    @GetMapping("/bills/trend")
    public R<java.util.List<java.util.Map<String, Object>>> billTrend(
            @RequestParam(defaultValue = "6") int months) {
        int window = Math.max(1, Math.min(months, 24));
        java.time.YearMonth end = java.time.YearMonth.now();
        java.util.List<java.util.Map<String, Object>> out = new java.util.ArrayList<>();
        for (int i = window - 1; i >= 0; i--) {
            java.time.YearMonth ym = end.minusMonths(i);
            String period = ym.toString();
            java.util.List<com.yundao.bp.fin.entity.FinBill> list =
                    billingService.listByPeriod(period);
            java.math.BigDecimal receivable = java.math.BigDecimal.ZERO;
            java.math.BigDecimal received = java.math.BigDecimal.ZERO;
            for (com.yundao.bp.fin.entity.FinBill b : list) {
                // 应收 = 账单金额 - 减免 + 滞纳金 - 豁免（不能用 payableAmount，
                // 它是「剩余应缴」，已缴清账单的 payable 为 0，会把应收算成 0）
                java.math.BigDecimal due = zero(b.getBillAmount())
                        .subtract(zero(b.getDiscountAmount()))
                        .add(zero(b.getLateFee()))
                        .subtract(zero(b.getWaivedAmount()));
                receivable = receivable.add(due);
                received = received.add(zero(b.getPaidAmount()));
            }
            java.util.Map<String, Object> m = new java.util.LinkedHashMap<>();
            m.put("month", period);
            m.put("receivable", receivable.setScale(2, java.math.RoundingMode.HALF_UP));
            m.put("received", received.setScale(2, java.math.RoundingMode.HALF_UP));
            m.put("bills", list.size());
            m.put("rate", receivable.signum() == 0 ? 0
                    : received.multiply(java.math.BigDecimal.valueOf(100))
                            .divide(receivable, 1, java.math.RoundingMode.HALF_UP));
            out.add(m);
        }
        return R.ok(out);
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

    private static java.math.BigDecimal zero(java.math.BigDecimal v) {
        return v == null ? java.math.BigDecimal.ZERO : v;
    }
}
