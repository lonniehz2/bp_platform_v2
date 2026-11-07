package com.yundao.bp.property.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.property.entity.PropProjectConfig;
import com.yundao.bp.property.service.PropertyProjectService;
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** 物业管理项目。 */
@RestController
@RequestMapping("/api/v1/property/projects")
public class PropertyProjectController {

    private final PropertyProjectService service;

    public PropertyProjectController(PropertyProjectService service) {
        this.service = service;
    }

    @com.yundao.bp.iam.security.RequirePerm("property:project:view")
    @GetMapping
    public R<List<PropProjectConfig>> list() {
        return R.ok(service.list());
    }

    @com.yundao.bp.iam.security.RequirePerm("property:project:manage")
    @PostMapping
    public R<PropProjectConfig> create(@RequestBody PropertyProjectService.CreateCmd cmd) {
        return R.ok(service.create(cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:project:manage")
    @PutMapping("/{orgId}")
    public R<PropProjectConfig> update(@PathVariable Long orgId,
                                       @RequestBody PropertyProjectService.UpdateCmd cmd) {
        return R.ok(service.update(orgId, cmd));
    }
}
