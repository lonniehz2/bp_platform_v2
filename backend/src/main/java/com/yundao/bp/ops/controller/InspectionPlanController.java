package com.yundao.bp.ops.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.iam.security.RequirePerm;
import com.yundao.bp.ops.dto.InspectionPlanCmd;
import com.yundao.bp.ops.entity.OpsInspectionPlan;
import com.yundao.bp.ops.service.InspectionPlanService;
import jakarta.validation.Valid;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** 物业巡检计划。 */
@RestController
@RequestMapping("/api/v1/ops/inspection-plans")
public class InspectionPlanController {

    private final InspectionPlanService service;

    public InspectionPlanController(InspectionPlanService service) {
        this.service = service;
    }

    @PostMapping
    @RequirePerm("ops:workorder:create")
    public R<OpsInspectionPlan> create(@Valid @RequestBody InspectionPlanCmd cmd) {
        return R.ok(service.create(cmd));
    }

    @GetMapping
    @RequirePerm("ops:workorder:view")
    public R<PageResult<OpsInspectionPlan>> page(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) String planStatus) {
        return R.ok(service.page(pageNum, pageSize, planStatus));
    }

    /** 手动触发到期巡检：为到期的计划生成工单。 */
    @PostMapping("/run-due")
    @RequirePerm("ops:workorder:create")
    public R<Map<String, Object>> runDue() {
        return R.ok(service.runDue());
    }
}
