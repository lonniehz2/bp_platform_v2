package com.yundao.bp.fin.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.fin.dto.PrepayPayInCmd;
import com.yundao.bp.fin.dto.PrepayRefundCmd;
import com.yundao.bp.fin.service.PrepayService;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** 合同预收余额。 */
@RestController
@RequestMapping("/api/v1/fin/prepay")
public class PrepayController {

    private final PrepayService service;

    public PrepayController(PrepayService service) {
        this.service = service;
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:payment:pay")
    @GetMapping("/{contractId}")
    public R<Map<String, Object>> account(@PathVariable Long contractId) {
        return R.ok(service.account(contractId));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:payment:pay")
    @PostMapping("/in")
    public R<Map<String, Object>> payIn(@RequestBody PrepayPayInCmd cmd) {
        return R.ok(service.payIn(cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:payment:refund")
    @PostMapping("/refund")
    public R<Map<String, Object>> refund(@RequestBody PrepayRefundCmd cmd) {
        return R.ok(service.refund(cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:payment:pay")
    @PostMapping("/apply/{contractId}")
    public R<Integer> apply(@PathVariable Long contractId) {
        return R.ok(service.applyToContract(contractId));
    }
}
