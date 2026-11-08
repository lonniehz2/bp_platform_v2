package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.GuaranteeDepositService;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/platform/guarantee")
public class GuaranteeDepositController {

    private final GuaranteeDepositService service;

    public GuaranteeDepositController(GuaranteeDepositService service) {
        this.service = service;
    }

    @GetMapping("/contracts/{contractId}/deposit")
    public R<Map<String, Object>> get(@PathVariable long contractId) {
        return R.ok(service.get(contractId));
    }

    @PostMapping("/contracts/{contractId}/deposit/pay")
    public R<Map<String, Object>> pay(@PathVariable long contractId,
                                      @RequestBody GuaranteeDepositService.PayCmd cmd) {
        return R.ok(service.pay(contractId, cmd));
    }

    @PostMapping("/deposits/{depositId}/refund")
    public R<Map<String, Object>> refund(@PathVariable long depositId,
                                         @RequestBody GuaranteeDepositService.RefundCmd cmd) {
        return R.ok(service.refund(depositId, cmd));
    }
}
