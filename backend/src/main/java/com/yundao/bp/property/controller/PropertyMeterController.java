package com.yundao.bp.property.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.property.service.PropertyMeterService;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** 物业水电抄表。 */
@RestController
@RequestMapping("/api/v1/property/meters")
public class PropertyMeterController {

    private final PropertyMeterService service;

    public PropertyMeterController(PropertyMeterService service) {
        this.service = service;
    }

    @com.yundao.bp.iam.security.RequirePerm("property:meter:view")
    @GetMapping
    public R<List<Map<String, Object>>> meters(@RequestParam Long projectId) {
        return R.ok(service.meters(projectId));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:meter:manage")
    @PostMapping
    public R<Map<String, Object>> create(@RequestParam Long projectId,
            @RequestBody PropertyMeterService.MeterCmd cmd) {
        return R.ok(service.createMeter(projectId, cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:meter:view")
    @GetMapping("/readings")
    public R<List<Map<String, Object>>> readings(@RequestParam Long projectId,
            @RequestParam(required = false) Long meterId) {
        return R.ok(service.readings(projectId, meterId));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:meter:manage")
    @PostMapping("/readings")
    public R<Map<String, Object>> reading(@RequestParam Long projectId,
            @RequestBody PropertyMeterService.ReadingCmd cmd) {
        return R.ok(service.addReading(projectId, cmd));
    }
}
