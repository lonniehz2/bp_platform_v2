package com.yundao.bp.property.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.property.service.PropertyDunningService;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** 物业欠费催缴。 */
@RestController
@RequestMapping("/api/v1/property/dunning")
public class PropertyDunningController {

    private final PropertyDunningService service;

    public PropertyDunningController(PropertyDunningService service) {
        this.service = service;
    }

    @com.yundao.bp.iam.security.RequirePerm("property:dunning:view")
    @GetMapping("/arrears")
    public R<List<Map<String, Object>>> arrears(@RequestParam Long projectId,
                                                @RequestParam(required = false) String keyword) {
        return R.ok(service.arrears(projectId, keyword));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:dunning:create")
    @PostMapping("/tasks")
    public R<Map<String, Object>> send(@RequestParam Long projectId,
            @RequestBody PropertyDunningService.SendCmd cmd) {
        return R.ok(service.send(projectId, cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:dunning:view")
    @GetMapping("/tasks")
    public R<List<Map<String, Object>>> tasks(@RequestParam Long projectId) {
        return R.ok(service.tasks(projectId));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:dunning:view")
    @GetMapping("/tasks/{taskId}/records")
    public R<List<Map<String, Object>>> records(@PathVariable Long taskId) {
        return R.ok(service.records(taskId));
    }
}
