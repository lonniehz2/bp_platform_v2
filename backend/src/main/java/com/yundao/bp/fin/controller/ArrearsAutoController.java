package com.yundao.bp.fin.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.fin.job.ArrearsAutoJob;
import java.util.Map;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** 欠费自动处置手工补跑。 */
@RestController
@RequestMapping("/api/v1/ops/arrears")
public class ArrearsAutoController {

    private final ArrearsAutoJob job;

    public ArrearsAutoController(ArrearsAutoJob job) {
        this.job = job;
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:arrear:execute")
    @PostMapping("/run")
    public R<Map<String, Object>> run() {
        return R.ok(job.runAll());
    }
}
