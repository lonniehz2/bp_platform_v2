package com.yundao.bp.property.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.property.service.PropertyUnitService;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** 物业房屋与业主关系。 */
@RestController
@RequestMapping("/api/v1/property/units")
public class PropertyUnitController {

    private final PropertyUnitService service;

    public PropertyUnitController(PropertyUnitService service) {
        this.service = service;
    }

    @com.yundao.bp.iam.security.RequirePerm("property:unit:view")
    @GetMapping("/buildings")
    public R<List<Map<String, Object>>> buildings(@RequestParam Long projectId) {
        return R.ok(service.buildings(projectId));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:unit:view")
    @GetMapping
    public R<List<Map<String, Object>>> units(@RequestParam Long projectId,
                                              @RequestParam(required = false) Long buildingId) {
        return R.ok(service.units(projectId, buildingId));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:owner:view")
    @GetMapping("/{houseId}/owners")
    public R<List<Map<String, Object>>> owners(@RequestParam Long projectId,
                                               @PathVariable Long houseId) {
        return R.ok(service.owners(projectId, houseId));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:owner:edit")
    @PostMapping("/{houseId}/owners")
    public R<Map<String, Object>> assignOwner(@RequestParam Long projectId,
                                              @PathVariable Long houseId,
            @RequestBody PropertyUnitService.OwnerCmd cmd) {
        return R.ok(service.assignOwner(projectId, houseId, cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:owner:edit")
    @DeleteMapping("/owners/{id}")
    public R<Map<String, Object>> removeOwner(@PathVariable Long id) {
        return R.ok(service.removeOwner(id));
    }
}
