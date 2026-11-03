package com.yundao.bp.fin.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.fin.service.FinanceReportService;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** 财务多口径汇总。 */
@RestController
@RequestMapping("/api/v1/fin")
public class FinanceReportController {

    private final FinanceReportService service;

    public FinanceReportController(FinanceReportService service) {
        this.service = service;
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:bill:view")
    @GetMapping("/finance-report")
    public R<Map<String, Object>> overview(@RequestParam String period) {
        return R.ok(service.overview(period));
    }
}
