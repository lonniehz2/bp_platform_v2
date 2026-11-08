package com.yundao.bp.property.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.property.service.PropertyInvoiceService;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** 物业电子发票申请。 */
@RestController
@RequestMapping("/api/v1/property/invoices")
public class PropertyInvoiceController {

    private final PropertyInvoiceService service;

    public PropertyInvoiceController(PropertyInvoiceService service) {
        this.service = service;
    }

    @com.yundao.bp.iam.security.RequirePerm("property:invoice:view")
    @GetMapping
    public R<List<Map<String, Object>>> list(@RequestParam Long projectId) {
        return R.ok(service.list(projectId));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:invoice:request")
    @PostMapping
    public R<Map<String, Object>> request(@RequestParam Long projectId,
            @RequestBody PropertyInvoiceService.InvoiceCmd cmd) {
        return R.ok(service.request(projectId, cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:invoice:issue")
    @PostMapping("/{id}/issue")
    public R<Map<String, Object>> issue(@PathVariable Long id) {
        return R.ok(service.issue(id));
    }
}
