package com.yundao.bp.property.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.property.service.PropertyLeaseService;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** 物业租赁合同。 */
@RestController
@RequestMapping("/api/v1/property/leases")
public class PropertyLeaseController {

    private final PropertyLeaseService service;

    public PropertyLeaseController(PropertyLeaseService service) {
        this.service = service;
    }

    @com.yundao.bp.iam.security.RequirePerm("property:lease:view")
    @GetMapping
    public R<List<Map<String, Object>>> list(@RequestParam Long projectId) {
        return R.ok(service.list(projectId));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:lease:manage")
    @PostMapping
    public R<Map<String, Object>> create(@RequestParam Long projectId,
            @RequestBody PropertyLeaseService.LeaseCmd cmd) {
        return R.ok(service.create(projectId, cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:lease:manage")
    @PostMapping("/{id}/generate")
    public R<Map<String, Object>> generate(@RequestParam Long projectId, @PathVariable Long id,
            @RequestBody(required = false) GenerateCmd cmd) {
        return R.ok(service.generate(projectId, id,
                cmd == null ? null : cmd.periodStart(), cmd == null ? null : cmd.periodEnd()));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:lease:manage")
    @PostMapping("/{id}/end")
    public R<Map<String, Object>> end(@RequestParam Long projectId, @PathVariable Long id) {
        return R.ok(service.end(projectId, id));
    }

    public record GenerateCmd(LocalDate periodStart, LocalDate periodEnd) {
    }
}
