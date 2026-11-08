package com.yundao.bp.property.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.property.service.PropertyParkingService;
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

/** 物业服务 - 车位管理。 */
@RestController
@RequestMapping("/api/v1/property/parking")
public class PropertyParkingController {

    private final PropertyParkingService service;

    public PropertyParkingController(PropertyParkingService service) {
        this.service = service;
    }

    @com.yundao.bp.iam.security.RequirePerm("property:parking:view")
    @GetMapping("/spaces")
    public R<List<Map<String, Object>>> spaces(@RequestParam Long projectId) {
        return R.ok(service.spaces(projectId));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:parking:manage")
    @PostMapping("/spaces")
    public R<Map<String, Object>> createSpace(@RequestParam Long projectId,
            @RequestBody PropertyParkingService.SpaceCmd cmd) {
        return R.ok(service.createSpace(projectId, cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:parking:view")
    @GetMapping("/rates")
    public R<List<Map<String, Object>>> rates(@RequestParam Long projectId) {
        return R.ok(service.rates(projectId));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:parking:manage")
    @PostMapping("/rates")
    public R<Map<String, Object>> createRate(@RequestParam Long projectId,
            @RequestBody PropertyParkingService.RateCmd cmd) {
        return R.ok(service.createRate(projectId, cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:parking:manage")
    @PostMapping("/plans")
    public R<Map<String, Object>> createPlan(@RequestBody PropertyParkingService.PlanCmd cmd) {
        return R.ok(service.createPlan(cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:parking:manage")
    @PostMapping("/plans/{id}/renew")
    public R<Map<String, Object>> renew(@PathVariable Long id,
            @RequestBody(required = false) RenewCmd cmd) {
        return R.ok(service.renew(id, cmd == null ? null : cmd.billingCycle(),
                cmd == null ? null : cmd.startDate()));
    }

    public record RenewCmd(String billingCycle, LocalDate startDate) {
    }

    @com.yundao.bp.iam.security.RequirePerm("property:parking:manage")
    @PostMapping("/plans/{id}/terminate")
    public R<Map<String, Object>> terminate(@PathVariable Long id,
            @RequestBody(required = false) TerminateCmd cmd) {
        return R.ok(service.terminate(id, cmd == null ? null : cmd.terminationDate()));
    }

    public record TerminateCmd(LocalDate terminationDate) {
    }
}
