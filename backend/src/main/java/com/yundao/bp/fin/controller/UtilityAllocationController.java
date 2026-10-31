package com.yundao.bp.fin.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.fin.dto.*;
import com.yundao.bp.fin.entity.EnergyPolicy;
import com.yundao.bp.fin.entity.MeterPoint;
import com.yundao.bp.fin.entity.UtilityAllocation;
import com.yundao.bp.fin.service.UtilityAllocationService;
import jakarta.validation.Valid;
import java.time.LocalDate;
import java.util.List;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/fin")
public class UtilityAllocationController {

    private final UtilityAllocationService service;

    public UtilityAllocationController(UtilityAllocationService service) {
        this.service = service;
    }

    @GetMapping("/meter-points")
    public R<List<MeterPoint>> points() {
        return R.ok(service.points());
    }

    @PostMapping("/meter-points")
    public R<MeterPoint> createPoint(@Valid @RequestBody MeterPointCmd cmd) {
        return R.ok(service.savePoint(null, cmd));
    }

    @PutMapping("/meter-points/{id}")
    public R<MeterPoint> updatePoint(@PathVariable Long id,
                                     @Valid @RequestBody MeterPointCmd cmd) {
        return R.ok(service.savePoint(id, cmd));
    }

    @PostMapping("/meter-points/{id}/readings")
    public R<Void> addReading(@PathVariable Long id, @RequestBody MeterReadCmd cmd) {
        service.addReading(id, cmd);
        return R.ok(null);
    }

    @PostMapping("/meter-points/{id}/read-now")
    public R<Void> readNow(@PathVariable Long id) {
        service.readNow(id);
        return R.ok(null);
    }

    @PostMapping("/utility-allocations/preview")
    public R<UtilityAllocationVO> preview(@RequestBody AllocCmd cmd) {
        return R.ok(service.preview(cmd.period(), cmd.meterPointId()));
    }

    @PostMapping("/utility-allocations/confirm")
    public R<UtilityAllocationVO> confirm(@RequestBody AllocCmd cmd) {
        if (!com.yundao.bp.common.tenant.TenantContext.hasTenant()
                && com.yundao.bp.iam.security.LoginUser.get() != null) {
            com.yundao.bp.iam.security.LoginUser u = com.yundao.bp.iam.security.LoginUser.get();
            com.yundao.bp.common.tenant.TenantContext.set(
                    com.yundao.bp.common.tenant.TenantInfo.of(u.tenantId(), u.userId()));
        }
        return R.ok(service.confirm(cmd.period(), cmd.meterPointId()));
    }

    @PostMapping("/utility-allocations/exit")
    public R<UtilityAllocationVO> exit(@RequestBody ExitCmd cmd) {
        if (!com.yundao.bp.common.tenant.TenantContext.hasTenant()
                && com.yundao.bp.iam.security.LoginUser.get() != null) {
            com.yundao.bp.iam.security.LoginUser u = com.yundao.bp.iam.security.LoginUser.get();
            com.yundao.bp.common.tenant.TenantContext.set(
                    com.yundao.bp.common.tenant.TenantInfo.of(u.tenantId(), u.userId()));
        }
        return R.ok(service.settleExit(cmd.meterPointId(), cmd.contractId(), cmd.exitDate(),
                cmd.reading()));
    }

    @GetMapping("/utility-allocations")
    public R<List<UtilityAllocation>> allocations(@RequestParam(required = false) String period) {
        return R.ok(service.allocations(period));
    }

    @GetMapping("/energy-analysis/monthly")
    public R<EnergyStatVO> monthly(@RequestParam String period,
                                   @RequestParam(required = false) Long feeItemId) {
        return R.ok(service.energyMonthly(period, feeItemId));
    }

    @GetMapping("/energy-policy")
    public R<EnergyPolicy> policy(@RequestParam(required = false) Long orgId) {
        return R.ok(service.policy(orgId));
    }

    @PutMapping("/energy-policy")
    public R<EnergyPolicy> savePolicy(@RequestBody EnergyPolicyCmd cmd) {
        return R.ok(service.savePolicy(cmd));
    }

    public record AllocCmd(String period, Long meterPointId) {
    }

    public record ExitCmd(Long meterPointId, Long contractId, LocalDate exitDate,
                          java.math.BigDecimal reading) {
    }
}
