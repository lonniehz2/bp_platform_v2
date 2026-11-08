package com.yundao.bp.property.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.property.service.PropertyEnergyService;
import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** 公共能耗分摊。 */
@RestController
@RequestMapping("/api/v1/property/energy")
public class PropertyEnergyController {

    private final PropertyEnergyService service;

    public PropertyEnergyController(PropertyEnergyService service) {
        this.service = service;
    }

    @com.yundao.bp.iam.security.RequirePerm("property:meter:view")
    @GetMapping("/allocations")
    public R<List<Map<String, Object>>> list(@RequestParam Long projectId,
            @RequestParam(required = false) String period) {
        return R.ok(service.list(projectId, period));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:meter:manage")
    @PostMapping("/allocations")
    public R<Map<String, Object>> allocate(@RequestParam Long projectId,
            @RequestBody AllocateCmd cmd) {
        return R.ok(service.allocate(projectId, cmd.period(), cmd.totalAmount(), cmd.feeItemId()));
    }

    public record AllocateCmd(String period, BigDecimal totalAmount, Long feeItemId) {
    }
}
