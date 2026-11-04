package com.yundao.bp.ops.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.ops.job.DailyPatrolJob;
import java.util.Map;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** 自动巡查手工补跑。 */
@RestController
@RequestMapping("/api/v1/ops/patrol")
public class PatrolController {

    private final DailyPatrolJob job;

    public PatrolController(DailyPatrolJob job) {
        this.job = job;
    }

    @com.yundao.bp.iam.security.RequirePerm("ops:alert:view")
    @PostMapping("/run")
    public R<Map<String, Object>> run() {
        return R.ok(job.runAll());
    }
}
