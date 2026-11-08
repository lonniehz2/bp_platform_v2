package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.BillingService;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/platform/billing")
public class BillingController {

    private final BillingService service;

    public BillingController(BillingService service) {
        this.service = service;
    }

    @GetMapping("/bills")
    public R<List<Map<String, Object>>> bills(@RequestParam long projectId,
                                              @RequestParam(required = false) String status) {
        return R.ok(service.bills(projectId, status));
    }

    @PostMapping("/bills/{billId}/pay")
    public R<Map<String, Object>> pay(@PathVariable long billId,
                                      @RequestBody BillingService.PaymentCmd cmd) {
        return R.ok(service.pay(billId, cmd));
    }

    @GetMapping("/payments")
    public R<List<Map<String, Object>>> payments(@RequestParam long projectId) {
        return R.ok(service.payments(projectId));
    }

    @GetMapping("/payments/{paymentId}/receipt")
    public R<Map<String, Object>> receipt(@PathVariable long paymentId) {
        return R.ok(service.receipt(paymentId));
    }
}
