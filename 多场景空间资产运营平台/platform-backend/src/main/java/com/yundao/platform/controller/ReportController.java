package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.ReportService;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/platform/reports")
public class ReportController {

    private final ReportService service;

    public ReportController(ReportService service) { this.service = service; }

    @GetMapping("/projects/compare")
    public R<List<Map<String, Object>>> compare() { return R.ok(service.projectCompare()); }

    @GetMapping("/projects/{projectId}/cockpit")
    public R<Map<String, Object>> cockpit(@PathVariable long projectId) { return R.ok(service.cockpit(projectId)); }
}
