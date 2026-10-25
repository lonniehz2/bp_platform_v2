package com.yundao.bp.fin.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.fin.dto.ArrearsActionCreateCmd;
import com.yundao.bp.fin.dto.ArrearsActionVO;
import com.yundao.bp.fin.service.ArrearsActionService;
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
 * 欠费停权处置接口（BC-08）。
 *
 * <p>⭐ <b>安全底线</b>：冻结默认保留大门门禁（{@code EXCLUDE_MAIN_DOOR}）；
 * 使用 {@code ALL} 停用大门须显式确认风险。
 */
@RestController
@RequestMapping("/api/v1/fin/arrears")
public class ArrearsActionController {

    private final ArrearsActionService service;

    /** 趋势统计复用账单服务 */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.fin.service.BillingService billingService;

    public ArrearsActionController(ArrearsActionService service) {
        this.service = service;
    }

    /** 欠费扫描（只给建议，不落库）。 */
    @com.yundao.bp.iam.security.RequirePerm("fin:arrear:scan")
    @GetMapping("/scan")
    public R<List<ArrearsActionService.ArrearsSuggestion>> scan(
            @RequestParam(defaultValue = "1") int minOverdueDays) {
        return R.ok(service.scanArrears(minOverdueDays));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:arrear:create")
    @PostMapping
    public R<ArrearsActionVO> create(@Valid @RequestBody ArrearsActionCreateCmd cmd) {
        return R.ok(service.create(cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:arrear:view")
    @GetMapping("/{id}")
    public R<ArrearsActionVO> get(@PathVariable Long id) {
        return R.ok(service.get(id));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:arrear:view")
    @GetMapping
    public R<PageResult<ArrearsActionVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                               @RequestParam(defaultValue = "20") long pageSize,
                                               @RequestParam(required = false) Long contractId,
                                               @RequestParam(required = false) Long personId,
                                               @RequestParam(required = false) String actionType,
                                               @RequestParam(required = false) String status) {
        return R.ok(service.page(pageNum, pageSize, contractId, personId, actionType, status));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:arrear:view")

    @GetMapping("/by-contract/{contractId}")
    public R<List<ArrearsActionVO>> byContract(@PathVariable Long contractId) {
        return R.ok(service.listByContract(contractId));
    }

    /** 执行处置。 */
    @com.yundao.bp.iam.security.RequirePerm("fin:arrear:execute")
    @PostMapping("/{id}/execute")
    public R<ArrearsActionVO> execute(@PathVariable Long id) {
        return R.ok(service.execute(id));
    }

    /** 撤销处置（已缴清）。 */
    @com.yundao.bp.iam.security.RequirePerm("fin:arrear:revoke")
    @PostMapping("/{id}/revoke")
    public R<ArrearsActionVO> revoke(@PathVariable Long id,
                                     @RequestBody(required = false) ReasonCmd cmd) {
        return R.ok(service.revoke(id, cmd == null ? null : cmd.reason()));
    }

    public record ReasonCmd(String reason) {
    }
    /**
     * 欠费趋势：近 N 个月逾期金额、逾期账单数、催缴动作数。
     *
     * <p>逾期口径：账单状态为 OVERDUE 或已过期仍未缴清的账单，
     * 按账单所属账期（yyyy-MM 或 yyyyMM）归月。
     */
    @com.yundao.bp.iam.security.RequirePerm("fin:bill:view")
    @GetMapping("/trend")
    public R<java.util.List<java.util.Map<String, Object>>> trend(
            @RequestParam(defaultValue = "6") int months) {
        int window = Math.max(1, Math.min(months, 24));
        java.time.YearMonth end = java.time.YearMonth.now();
        java.util.List<java.util.Map<String, Object>> out = new java.util.ArrayList<>();
        for (int i = window - 1; i >= 0; i--) {
            java.time.YearMonth ym = end.minusMonths(i);
            String period = ym.toString();
            java.util.List<com.yundao.bp.fin.entity.FinBill> bills =
                    billingService.listByPeriod(period);
            java.math.BigDecimal overdue = java.math.BigDecimal.ZERO;
            int overdueCount = 0;
            for (com.yundao.bp.fin.entity.FinBill b : bills) {
                boolean isOverdue = "OVERDUE".equals(b.getBillStatus())
                        || (("UNPAID".equals(b.getBillStatus())
                                || "PARTIAL".equals(b.getBillStatus()))
                            && b.getDueDate() != null
                            && b.getDueDate().isBefore(java.time.LocalDate.now()));
                if (!isOverdue) {
                    continue;
                }
                overdueCount++;
                java.math.BigDecimal pending = b.getPayableAmount() == null
                        ? java.math.BigDecimal.ZERO : b.getPayableAmount();
                if (b.getPaidAmount() != null) {
                    pending = pending.subtract(b.getPaidAmount());
                }
                if (pending.signum() > 0) {
                    overdue = overdue.add(pending);
                }
            }
            long actions = billingService.countArrearsActions(period);
            java.util.Map<String, Object> m = new java.util.LinkedHashMap<>();
            m.put("month", period);
            m.put("overdueAmount", overdue.setScale(2, java.math.RoundingMode.HALF_UP));
            m.put("overdueBills", overdueCount);
            m.put("actions", actions);
            out.add(m);
        }
        return R.ok(out);
    }
}
