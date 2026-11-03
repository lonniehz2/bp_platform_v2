package com.yundao.bp.fin.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.fin.dto.GenerateBatchCmd;
import com.yundao.bp.fin.dto.GenerateBatchVO;
import com.yundao.bp.fin.dto.GenerateBillsCmd;
import com.yundao.bp.fin.dto.GenerateResultVO;
import com.yundao.bp.fin.dto.RecalcBillsCmd;
import com.yundao.bp.fin.dto.RecalcBillsResult;
import com.yundao.bp.fin.dto.BillExplainVO;
import com.yundao.bp.fin.service.BillGenerationService;
import com.yundao.bp.fin.job.AutoBillingJob;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 批量自动出账接口（BC-08）。
 *
 * <p>用法：先 {@code dryRun=true} 试算核对金额，确认后 {@code dryRun=false} 落库。
 * 幂等：同「合同+收费项目+账期」已存在账单会跳过，可安全重复执行。
 */
@RestController
@RequestMapping("/api/v1/fin")
public class BillGenerationController {

    private final BillGenerationService service;
    private final AutoBillingJob autoBillingJob;

    public BillGenerationController(BillGenerationService service,
                                    AutoBillingJob autoBillingJob) {
        this.service = service;
        this.autoBillingJob = autoBillingJob;
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:bill:create")
    @PostMapping("/bills/generate")
    public R<GenerateResultVO> generate(@Valid @RequestBody GenerateBillsCmd cmd) {
        return R.ok(service.generate(cmd));
    }

    /**
     * 多项目批量出账（一次生成租金 + 物业费等多张账单）。
     *
     * <p>项目间相互隔离，单项失败不影响其它项，结果逐项返回。
     */
    /** 账单计费明细。 */
    @com.yundao.bp.iam.security.RequirePerm("fin:bill:view")
    @org.springframework.web.bind.annotation.GetMapping("/bills/{id}/explain")
    public R<BillExplainVO> explain(@org.springframework.web.bind.annotation.PathVariable Long id) {
        return R.ok(service.explain(id));
    }

    /** 历史账单按新规则重算（dryRun 预览）。 */
    @com.yundao.bp.iam.security.RequirePerm("fin:bill:batch")
    @PostMapping("/bills/recalculate")
    public R<RecalcBillsResult> recalculate(@RequestBody RecalcBillsCmd cmd) {
        return R.ok(service.recalculate(cmd));
    }

    /** 手工触发自动出账（补跑/运维）。 */
    @com.yundao.bp.iam.security.RequirePerm("fin:bill:batch")
    @PostMapping("/bills/auto-run")
    public R<Integer> autoRun() {
        return R.ok(autoBillingJob.runNow());
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:bill:batch")
    @PostMapping("/bills/generate-batch")
    public R<GenerateBatchVO> generateBatch(@Valid @RequestBody GenerateBatchCmd cmd) {
        return R.ok(service.generateBatch(cmd));
    }
}
