package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.GuaranteeSubsidyService;
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
public class GuaranteeSubsidyController {

    private final GuaranteeSubsidyService service;

    public GuaranteeSubsidyController(GuaranteeSubsidyService service) {
        this.service = service;
    }

    @GetMapping("/contracts/{contractId}/subsidies")
    public R<List<Map<String, Object>>> list(@PathVariable long contractId) {
        return R.ok(service.list(contractId));
    }

    @PostMapping("/contracts/{contractId}/subsidies")
    public R<Map<String, Object>> create(@PathVariable long contractId,
                                         @RequestBody GuaranteeSubsidyService.SubsidyCmd cmd) {
        return R.ok(service.create(contractId, cmd));
    }
}
