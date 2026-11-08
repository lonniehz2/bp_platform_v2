package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.DashboardService;
import java.time.LocalDate;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/platform/dashboard")
public class DashboardController {

    private final DashboardService service;

    public DashboardController(DashboardService service) {
        this.service = service;
    }

    @GetMapping("/summary")
    public R<Map<String, Object>> summary(@RequestParam long projectId,
                                          @RequestParam String dateFrom,
                                          @RequestParam String dateTo) {
        return R.ok(service.summary(projectId, LocalDate.parse(dateFrom), LocalDate.parse(dateTo)));
    }
}
