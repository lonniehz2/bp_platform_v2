package com.yundao.bp.fin.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.fin.dto.CashFlowRecordCmd;
import com.yundao.bp.fin.dto.CashFlowVO;
import com.yundao.bp.fin.dto.DunningCreateCmd;
import com.yundao.bp.fin.dto.DunningVO;
import com.yundao.bp.fin.dto.ReconcileCreateCmd;
import com.yundao.bp.fin.dto.ReconcileVO;
import com.yundao.bp.fin.service.CashFlowService;
import com.yundao.bp.fin.service.DunningService;
import com.yundao.bp.fin.service.ReconcileService;
import jakarta.validation.Valid;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 催缴 / 对账 / 资金流水接口（BC-08 资金账务收尾）。
 */
@RestController
@RequestMapping("/api/v1/fin")
public class FinLedgerController {

    private final DunningService dunningService;
    private final ReconcileService reconcileService;
    private final CashFlowService cashFlowService;

    public FinLedgerController(DunningService dunningService,
                               ReconcileService reconcileService,
                               CashFlowService cashFlowService) {
        this.dunningService = dunningService;
        this.reconcileService = reconcileService;
        this.cashFlowService = cashFlowService;
    }

    // ==================== 催缴 ====================

    /** 逾期账单催缴建议。 */
    @GetMapping("/dunnings/scan")
    public R<List<DunningService.DunningSuggestion>> scanDunning(
            @RequestParam(defaultValue = "3") int minOverdueDays,
            @RequestParam(defaultValue = "3") int maxDunningTimes) {
        return R.ok(dunningService.scanNeedDunning(minOverdueDays, maxDunningTimes));
    }

    @PostMapping("/dunnings")
    public R<DunningVO> createDunning(@Valid @RequestBody DunningCreateCmd cmd) {
        return R.ok(dunningService.create(cmd));
    }

    @GetMapping("/dunnings/{id}")
    public R<DunningVO> getDunning(@PathVariable Long id) {
        return R.ok(dunningService.get(id));
    }

    @GetMapping("/dunnings")
    public R<PageResult<DunningVO>> pageDunning(@RequestParam(defaultValue = "1") long pageNum,
                                                @RequestParam(defaultValue = "20") long pageSize,
                                                @RequestParam(required = false) Long billId,
                                                @RequestParam(required = false) Long personId,
                                                @RequestParam(required = false) String dunningType) {
        return R.ok(dunningService.page(pageNum, pageSize, billId, personId, dunningType));
    }

    @GetMapping("/dunnings/by-bill/{billId}")
    public R<List<DunningVO>> dunningByBill(@PathVariable Long billId) {
        return R.ok(dunningService.listByBill(billId));
    }

    // ==================== 对账 ====================

    @PostMapping("/reconciles")
    public R<ReconcileVO> createReconcile(@Valid @RequestBody ReconcileCreateCmd cmd) {
        return R.ok(reconcileService.create(cmd));
    }

    @GetMapping("/reconciles/{id}")
    public R<ReconcileVO> getReconcile(@PathVariable Long id) {
        return R.ok(reconcileService.get(id));
    }

    @GetMapping("/reconciles")
    public R<PageResult<ReconcileVO>> pageReconcile(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateFrom,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateTo,
            @RequestParam(required = false) String reconcileType,
            @RequestParam(required = false) String status) {
        return R.ok(reconcileService.page(pageNum, pageSize, dateFrom, dateTo, reconcileType,
                status));
    }

    /** 处理对账差异。 */
    @PostMapping("/reconciles/{id}/handle")
    public R<ReconcileVO> handleReconcile(@PathVariable Long id,
                                          @RequestBody(required = false) RemarkCmd cmd) {
        return R.ok(reconcileService.handle(id, cmd == null ? null : cmd.remark()));
    }

    // ==================== 资金流水 ====================

    /** 手工登记流水。 */
    @PostMapping("/cash-flows")
    public R<CashFlowVO> recordFlow(@Valid @RequestBody CashFlowRecordCmd cmd) {
        return R.ok(cashFlowService.recordManual(cmd));
    }

    @GetMapping("/cash-flows/{id}")
    public R<CashFlowVO> getFlow(@PathVariable Long id) {
        return R.ok(cashFlowService.get(id));
    }

    @GetMapping("/cash-flows")
    public R<PageResult<CashFlowVO>> pageFlow(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) String flowType,
            @RequestParam(required = false) String bizType,
            @RequestParam(required = false) Long bizId,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateFrom,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateTo) {
        return R.ok(cashFlowService.page(pageNum, pageSize, flowType, bizType, bizId,
                dateFrom, dateTo));
    }

    /** 期间净流入。 */
    @GetMapping("/cash-flows/net")
    public R<BigDecimal> netFlow(
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateFrom,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateTo) {
        return R.ok(cashFlowService.netAmount(dateFrom, dateTo));
    }

    /** 校验流水。 */
    @PostMapping("/cash-flows/{id}/verify")
    public R<CashFlowVO> verifyFlow(@PathVariable Long id,
                                     @RequestBody(required = false) RemarkCmd cmd) {
        return R.ok(cashFlowService.verify(id, cmd == null ? null : cmd.remark()));
    }

    public record RemarkCmd(String remark) {
    }
}
