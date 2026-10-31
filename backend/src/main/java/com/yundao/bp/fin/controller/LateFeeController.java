package com.yundao.bp.fin.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.fin.dto.LateFeePolicyCmd;
import com.yundao.bp.fin.entity.LateFeePolicy;
import com.yundao.bp.fin.service.LateFeeService;
import java.time.LocalDate;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/fin")
public class LateFeeController {

    private final LateFeeService service;

    public LateFeeController(LateFeeService service) {
        this.service = service;
    }

    @GetMapping("/late-fee-policy")
    public R<LateFeePolicy> policy(@RequestParam(required = false) Long orgId) {
        return R.ok(service.policy(orgId));
    }

    @PutMapping("/late-fee-policy")
    public R<LateFeePolicy> save(@RequestBody LateFeePolicyCmd cmd) {
        return R.ok(service.savePolicy(cmd));
    }

    @PostMapping("/late-fees/run")
    public R<Integer> run(@RequestParam(required = false) String date,
                          @RequestParam(required = false) Long billId) {
        return R.ok(service.calculate(date == null || date.isBlank()
                ? LocalDate.now() : LocalDate.parse(date), billId));
    }
}
