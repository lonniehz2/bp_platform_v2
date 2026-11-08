package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.WorkOrderService;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/platform/guarantee/work-orders")
public class WorkOrderController {

    private final WorkOrderService service;

    public WorkOrderController(WorkOrderService service) {
        this.service = service;
    }

    @GetMapping
    public R<List<Map<String, Object>>> list(@RequestParam long projectId) {
        return R.ok(service.list(projectId));
    }

    @PostMapping
    public R<Map<String, Object>> create(@RequestBody WorkOrderService.CreateCmd cmd) {
        return R.ok(service.create(cmd));
    }

    @PostMapping("/{orderId}/update")
    public R<Map<String, Object>> update(@PathVariable long orderId,
                                         @RequestBody WorkOrderService.UpdateCmd cmd) {
        return R.ok(service.update(orderId, cmd));
    }
}
