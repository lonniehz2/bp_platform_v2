package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.DeviceImportService;
import com.yundao.platform.service.DeviceService;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/platform/devices")
public class DeviceController {

    private final DeviceService service;
    private final DeviceImportService importService;
    private final com.yundao.platform.service.PermissionService permissions;

    public DeviceController(DeviceService service, DeviceImportService importService,
                            com.yundao.platform.service.PermissionService permissions) {
        this.service = service;
        this.importService = importService;
        this.permissions = permissions;
    }

    @GetMapping
    public R<List<Map<String, Object>>> list(@RequestParam long projectId) {
        return R.ok(service.list(projectId));
    }

    @PostMapping("/{deviceId}/bind")
    public R<Map<String, Object>> bind(@org.springframework.web.bind.annotation.PathVariable long deviceId,
                                       @RequestBody Map<String, Long> body) {
        permissions.require("device:bind");
        return R.ok(service.bind(deviceId, body.get("spaceId")));
    }

    @PostMapping("/import")
    public R<Map<String, Object>> importCsv(
            @org.springframework.web.bind.annotation.RequestParam("file")
            org.springframework.web.multipart.MultipartFile file) {
        permissions.require("device:import");
        return R.ok(importService.importCsv(file));
    }

    @PostMapping
    public R<Map<String, Object>> create(@RequestBody DeviceService.DeviceCmd cmd) {
        return R.ok(service.create(cmd));
    }
}
