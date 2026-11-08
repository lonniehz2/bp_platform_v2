package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.service.GuaranteeApplicationService;
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
@RequestMapping("/api/v1/platform/guarantee")
public class GuaranteeApplicationController {

    private final GuaranteeApplicationService service;
    private final com.yundao.platform.service.PermissionService permissions;

    public GuaranteeApplicationController(GuaranteeApplicationService service,
                                          com.yundao.platform.service.PermissionService permissions) {
        this.service = service;
        this.permissions = permissions;
    }

    @GetMapping("/applications")
    public R<List<Map<String, Object>>> list(@RequestParam long projectId) {
        return R.ok(service.list(projectId));
    }

    @PostMapping("/applications")
    public R<Map<String, Object>> create(@RequestBody GuaranteeApplicationService.ApplicationCmd cmd) {
        return R.ok(service.create(cmd));
    }

    @PostMapping("/applications/{applicationId}/submit")
    public R<Map<String, Object>> submit(@PathVariable long applicationId) {
        return R.ok(service.submit(applicationId));
    }

    @PostMapping("/applications/{applicationId}/approve")
    public R<Map<String, Object>> approve(@PathVariable long applicationId,
                                          @RequestBody(required = false) Map<String, String> body) {
        String comment = body == null ? null : body.get("comment");
        return R.ok(service.approve(applicationId, comment));
    }

    @PostMapping("/applications/{applicationId}/waitlist")
    public R<Map<String, Object>> waitlist(@PathVariable long applicationId) {
        permissions.require("application:waitlist");
        return R.ok(service.joinWaitlist(applicationId));
    }

    @GetMapping("/waitlist")
    public R<List<Map<String, Object>>> listWaitlist(@RequestParam long projectId) {
        return R.ok(service.listWaitlist(projectId));
    }

    @PostMapping("/waitlist/{waitlistId}/allocate")
    public R<Map<String, Object>> allocate(@PathVariable long waitlistId,
                                           @RequestBody Map<String, Long> body) {
        Long houseId = body.get("houseId");
        if (houseId == null) {
            throw BizException.param("houseId 不能为空");
        }
        return R.ok(service.allocate(waitlistId, houseId));
    }

    @GetMapping("/allocations")
    public R<List<Map<String, Object>>> allocations(@RequestParam long projectId) {
        return R.ok(service.allocations(projectId));
    }
}
