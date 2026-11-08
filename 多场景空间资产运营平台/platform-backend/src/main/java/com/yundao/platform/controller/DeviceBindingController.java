package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.DeviceBindingService;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/platform/projects/{projectId}/device-bindings")
public class DeviceBindingController {

    private final DeviceBindingService service;

    public DeviceBindingController(DeviceBindingService service) {
        this.service = service;
    }

    @GetMapping
    public R<Map<String, Object>> view(@PathVariable long projectId,
                                       @RequestParam long spaceId) {
        return R.ok(service.view(projectId, spaceId));
    }
}
