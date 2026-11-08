package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.GuaranteeContractChangeService;
import com.yundao.platform.service.WorkflowService;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/platform/guarantee")
public class GuaranteeContractChangeController {

    private final GuaranteeContractChangeService service;

    public GuaranteeContractChangeController(GuaranteeContractChangeService service) {
        this.service = service;
    }

    @GetMapping("/contracts/{contractId}/changes")
    public R<List<Map<String, Object>>> list(@PathVariable long contractId) {
        return R.ok(service.list(contractId));
    }

    @PostMapping("/contracts/{contractId}/changes")
    public R<Map<String, Object>> create(@PathVariable long contractId,
                                         @RequestBody GuaranteeContractChangeService.ChangeCmd cmd) {
        return R.ok(service.create(contractId, cmd));
    }

    @PostMapping("/contract-changes/{changeId}/submit")
    public R<Map<String, Object>> submit(@PathVariable long changeId) {
        return R.ok(service.submit(changeId));
    }

    @PostMapping("/contract-changes/{changeId}/approve")
    public R<Map<String, Object>> approve(@PathVariable long changeId,
                                          @RequestBody WorkflowService.ActionCmd cmd) {
        return R.ok(service.approve(changeId, cmd));
    }

    @PostMapping("/contract-changes/{changeId}/reject")
    public R<Map<String, Object>> reject(@PathVariable long changeId,
                                         @RequestBody WorkflowService.ActionCmd cmd) {
        return R.ok(service.reject(changeId, cmd));
    }
}
