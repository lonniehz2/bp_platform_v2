package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.ReceiptTemplateService;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/platform/receipt-templates")
public class ReceiptTemplateController {
    private final ReceiptTemplateService service;
    private final com.yundao.platform.service.PermissionService permissions;

    public ReceiptTemplateController(ReceiptTemplateService service, com.yundao.platform.service.PermissionService permissions) {
        this.service = service;
        this.permissions = permissions;
    }

    @GetMapping
    public R<List<Map<String, Object>>> list() { permissions.require("billing:view"); return R.ok(service.list()); }

    @PostMapping
    public R<Map<String, Object>> create(@RequestBody ReceiptTemplateService.Cmd cmd) { permissions.require("billing:adjust"); return R.ok(service.create(cmd.templateName(), cmd.configJson())); }

    @PostMapping("/{id}")
    public R<Map<String, Object>> update(@PathVariable long id, @RequestBody ReceiptTemplateService.Cmd cmd) { permissions.require("billing:adjust"); return R.ok(service.update(id, cmd.templateName(), cmd.configJson())); }

    @PostMapping("/{id}/publish")
    public R<Map<String, Object>> publish(@PathVariable long id) { permissions.require("billing:adjust"); return R.ok(service.publish(id)); }
}
