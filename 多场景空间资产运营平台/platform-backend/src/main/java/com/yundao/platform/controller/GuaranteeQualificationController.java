package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.GuaranteeQualificationService;
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
public class GuaranteeQualificationController {

    private final GuaranteeQualificationService service;

    public GuaranteeQualificationController(GuaranteeQualificationService service) {
        this.service = service;
    }

    @GetMapping("/contracts/{contractId}/qualification-reviews")
    public R<List<Map<String, Object>>> list(@PathVariable long contractId) {
        return R.ok(service.list(contractId));
    }

    @PostMapping("/contracts/{contractId}/qualification-reviews")
    public R<Map<String, Object>> create(@PathVariable long contractId,
                                         @RequestBody GuaranteeQualificationService.ReviewCmd cmd) {
        return R.ok(service.create(contractId, cmd));
    }

    @PostMapping("/qualification-reviews/{reviewId}/complete")
    public R<Map<String, Object>> complete(@PathVariable long reviewId,
                                           @RequestBody GuaranteeQualificationService.CompleteCmd cmd) {
        return R.ok(service.complete(reviewId, cmd));
    }
}
