package com.yundao.bp.fin.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.fin.service.BillMigrationService;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** 历史跨月账单迁移。 */
@RestController
@RequestMapping("/api/v1/fin/bills")
public class BillMigrationController {

    private final BillMigrationService service;

    public BillMigrationController(BillMigrationService service) {
        this.service = service;
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:bill:batch")
    @GetMapping("/cross-month-preview")
    public R<List<Map<String, Object>>> preview() {
        return R.ok(service.preview());
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:bill:batch")
    @PostMapping("/split-cross-month")
    public R<Map<String, Object>> split(@RequestParam(defaultValue = "true") boolean dryRun) {
        return R.ok(service.splitUnpaid(dryRun));
    }
}
