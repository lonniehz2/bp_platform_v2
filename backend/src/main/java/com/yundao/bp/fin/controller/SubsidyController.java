package com.yundao.bp.fin.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.fin.dto.SubsidyCalcCmd;
import com.yundao.bp.fin.dto.SubsidyGrantCmd;
import com.yundao.bp.fin.dto.SubsidyRecordVO;
import com.yundao.bp.fin.dto.SubsidyStandardCreateCmd;
import com.yundao.bp.fin.dto.SubsidyStandardVO;
import com.yundao.bp.fin.service.SubsidyService;
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
 * 补贴标准与发放接口（BC-08，广州双轨支撑）。
 */
@RestController
@RequestMapping("/api/v1/fin/subsidies")
public class SubsidyController {

    private final SubsidyService service;

    public SubsidyController(SubsidyService service) {
        this.service = service;
    }

    // ---------- 标准 ----------

    @com.yundao.bp.iam.security.RequirePerm("fin:subsidy:create")
    @PostMapping("/standards")
    public R<SubsidyStandardVO> createStandard(@Valid @RequestBody SubsidyStandardCreateCmd cmd) {
        return R.ok(service.createStandard(cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:subsidy:view")
    @GetMapping("/standards/{id}")
    public R<SubsidyStandardVO> getStandard(@PathVariable Long id) {
        return R.ok(service.getStandard(id));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:subsidy:view")
    @GetMapping("/standards")
    public R<PageResult<SubsidyStandardVO>> pageStandards(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) String securityType,
            @RequestParam(required = false) String subsidyMode,
            @RequestParam(required = false) String keyword) {
        return R.ok(service.pageStandards(pageNum, pageSize, securityType, subsidyMode, keyword));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:subsidy:status")
    @PostMapping("/standards/{id}/status")
    public R<SubsidyStandardVO> setStatus(@PathVariable Long id,
                                          @RequestBody StatusCmd cmd) {
        return R.ok(service.setStandardStatus(id, cmd.enabled()));
    }

    /** 补贴试算（不落库）。 */
    @com.yundao.bp.iam.security.RequirePerm("fin:subsidy:calc")
    @PostMapping("/calc")
    public R<SubsidyService.SubsidyCalcResult> calc(@Valid @RequestBody SubsidyCalcCmd cmd,
            @org.springframework.web.bind.annotation.RequestParam(required = false) String period) {
        return R.ok(service.preview(cmd, period));
    }

    // ---------- 发放 ----------

    @com.yundao.bp.iam.security.RequirePerm("fin:subsidy:record")
    @PostMapping("/records")
    public R<SubsidyRecordVO> grant(@Valid @RequestBody SubsidyGrantCmd cmd) {
        return R.ok(service.grant(cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:subsidy:record")
    @GetMapping("/records/{id}")
    public R<SubsidyRecordVO> getRecord(@PathVariable Long id) {
        return R.ok(service.getRecord(id));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:subsidy:record")
    @GetMapping("/records")
    public R<PageResult<SubsidyRecordVO>> pageRecords(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) Long contractId,
            @RequestParam(required = false) Long personId,
            @RequestParam(required = false) String period,
            @RequestParam(required = false) String status) {
        return R.ok(service.pageRecords(pageNum, pageSize, contractId, personId, period, status));
    }

    /** 批量发放。 */
    @com.yundao.bp.iam.security.RequirePerm("fin:subsidy:record")
    @PostMapping("/records/batch")
    public R<SubsidyService.BatchResult> grantBatch(@RequestBody BatchCmd cmd) {
        return R.ok(service.grantBatch(cmd.subsidyPeriod(), cmd.orgId(), cmd.payMode(),
                cmd.dryRun() != null && cmd.dryRun()));
    }

    /** 确认发放（OFFSET_RENT 会抵扣当期租金账单）。 */
    @com.yundao.bp.iam.security.RequirePerm("fin:subsidy:record")
    @PostMapping("/records/{id}/confirm")
    public R<SubsidyRecordVO> confirm(@PathVariable Long id, @RequestBody(required = false) ConfirmCmd cmd) {
        return R.ok(service.confirmPaid(id, cmd == null ? null : cmd.paidAmount(),
                cmd == null ? null : cmd.financeBatchNo()));
    }

    /** 标记发放失败。 */
    @com.yundao.bp.iam.security.RequirePerm("fin:subsidy:record")
    @PostMapping("/records/{id}/fail")
    public R<SubsidyRecordVO> fail(@PathVariable Long id,
                                   @RequestBody(required = false) ReasonCmd cmd) {
        return R.ok(service.markFailed(id, cmd == null ? null : cmd.reason()));
    }

    public record StatusCmd(boolean enabled) {
    }

    public record BatchCmd(String subsidyPeriod, Long orgId, String payMode, Boolean dryRun) {
    }

    public record ConfirmCmd(BigDecimal paidAmount, String financeBatchNo) {
    }

    public record ReasonCmd(String reason) {
    }
}
