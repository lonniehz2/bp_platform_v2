package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.BillingService;
import com.yundao.platform.service.GuaranteeContractService;
import com.yundao.platform.service.TerminationSettlementService;
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

@RestController
@RequestMapping("/api/v1/platform/guarantee/contracts")
public class GuaranteeContractController {

    private final GuaranteeContractService contractService;
    private final BillingService billingService;
    private final com.yundao.platform.service.PermissionService permissions;
    private final TerminationSettlementService terminationSettlement;

    public GuaranteeContractController(GuaranteeContractService contractService,
                                       BillingService billingService,
                                       com.yundao.platform.service.PermissionService permissions,
                                       TerminationSettlementService terminationSettlement) {
        this.contractService = contractService;
        this.billingService = billingService;
        this.permissions = permissions;
        this.terminationSettlement = terminationSettlement;
    }

    @GetMapping
    public R<List<Map<String, Object>>> list(@RequestParam long projectId) {
        return R.ok(contractService.list(projectId));
    }

    @PostMapping
    public R<Map<String, Object>> create(@RequestBody GuaranteeContractService.ContractCmd cmd) {
        return R.ok(contractService.create(cmd));
    }

    @PostMapping("/{contractId}/submit")
    public R<Map<String, Object>> submit(@PathVariable long contractId) {
        permissions.require("contract:submit");
        return R.ok(contractService.submit(contractId));
    }

    @PostMapping("/{contractId}/approve")
    public R<Map<String, Object>> approve(@PathVariable long contractId) {
        permissions.require("contract:approve");
        return R.ok(contractService.approve(contractId));
    }

    @PostMapping("/{contractId}/activate")
    public R<Map<String, Object>> activate(@PathVariable long contractId,
                                           @RequestBody(required = false) Map<String, String> body) {
        permissions.require("contract:activate");
        return R.ok(contractService.activate(contractId, body == null ? null : body.get("reason")));
    }

    @PostMapping("/{contractId}/withdraw")
    public R<Map<String, Object>> withdraw(@PathVariable long contractId) {
        permissions.require("contract:withdraw");
        return R.ok(contractService.withdraw(contractId));
    }

    @PostMapping("/{contractId}/renew")
    public R<Map<String, Object>> renew(@PathVariable long contractId,
                                        @RequestBody GuaranteeContractService.RenewCmd cmd) {
        permissions.require("contract:submit");
        return R.ok(contractService.renew(contractId, cmd));
    }

    @PostMapping("/{contractId}/discard")
    public R<Map<String, Object>> discard(@PathVariable long contractId) {
        permissions.require("contract:discard");
        return R.ok(contractService.discard(contractId));
    }

    @GetMapping("/{contractId}/termination-settlement")
    public R<Map<String, Object>> settlementPreview(@PathVariable long contractId) {
        permissions.require("contract:submit");
        return R.ok(terminationSettlement.preview(contractId));
    }

    @PostMapping("/{contractId}/termination-settlement")
    public R<Map<String, Object>> settle(@PathVariable long contractId,
                                         @RequestBody(required = false) Map<String, String> body) {
        permissions.require("contract:submit");
        LocalDate date = body == null || body.get("date") == null || body.get("date").isBlank()
                ? LocalDate.now() : LocalDate.parse(body.get("date"));
        return R.ok(terminationSettlement.settle(contractId, date, body == null ? null : body.get("reason")));
    }

    @PostMapping("/{contractId}/bills")
    public R<Map<String, Object>> generateBill(@PathVariable long contractId,
                                               @RequestBody BillingService.BillCmd cmd) {
        return R.ok(billingService.generate(contractId, cmd));
    }
}
