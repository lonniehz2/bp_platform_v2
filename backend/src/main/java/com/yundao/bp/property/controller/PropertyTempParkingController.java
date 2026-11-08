package com.yundao.bp.property.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.property.service.PropertyTempParkingService;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** 临时停车。 */
@RestController
@RequestMapping("/api/v1/property/parking/temporary")
public class PropertyTempParkingController {

    private final PropertyTempParkingService service;

    public PropertyTempParkingController(PropertyTempParkingService service) {
        this.service = service;
    }

    @com.yundao.bp.iam.security.RequirePerm("property:parking:view")
    @GetMapping
    public R<List<Map<String, Object>>> list(@RequestParam Long projectId,
            @RequestParam(required = false) String status) {
        return R.ok(service.list(projectId, status));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:parking:manage")
    @PostMapping
    public R<Map<String, Object>> entry(@RequestParam Long projectId,
            @RequestBody PropertyTempParkingService.EntryCmd cmd) {
        return R.ok(service.entry(projectId, cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:parking:manage")
    @PostMapping("/{id}/exit")
    public R<Map<String, Object>> exit(@RequestParam Long projectId, @PathVariable Long id,
            @RequestBody ExitCmd cmd) {
        return R.ok(service.exit(projectId, id, cmd == null ? null : cmd.exitTime()));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:parking:manage")
    @PostMapping("/{id}/pay")
    public R<Map<String, Object>> pay(@RequestParam Long projectId, @PathVariable Long id,
            @RequestBody PayCmd cmd) {
        return R.ok(service.pay(projectId, id, cmd == null ? "CASH" : cmd.payMethod()));
    }

    public record ExitCmd(LocalDateTime exitTime) {
    }

    public record PayCmd(String payMethod) {
    }
}
