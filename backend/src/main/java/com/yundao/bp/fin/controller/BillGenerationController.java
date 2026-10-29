package com.yundao.bp.fin.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.fin.dto.GenerateBatchCmd;
import com.yundao.bp.fin.dto.GenerateBatchVO;
import com.yundao.bp.fin.dto.GenerateBillsCmd;
import com.yundao.bp.fin.dto.GenerateResultVO;
import com.yundao.bp.fin.dto.RecalcBillsCmd;
import com.yundao.bp.fin.dto.RecalcBillsResult;
import com.yundao.bp.fin.service.BillGenerationService;
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

    public BillGenerationController(BillGenerationService service) {
        this.service = service;
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
    /** 历史账单按新规则重算（dryRun 预览）。 */
    @com.yundao.bp.iam.security.RequirePerm("fin:bill:batch")
    @PostMapping("/bills/recalculate")
    public R<RecalcBillsResult> recalculate(@RequestBody RecalcBillsCmd cmd) {
        return R.ok(service.recalculate(cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:bill:batch")
    @PostMapping("/bills/generate-batch")
    public R<GenerateBatchVO> generateBatch(@Valid @RequestBody GenerateBatchCmd cmd) {
        return R.ok(service.generateBatch(cmd));
    }
}
