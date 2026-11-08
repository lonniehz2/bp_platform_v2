package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.GuaranteeContractService;
import java.util.Map;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/platform/guarantee/allocations")
public class GuaranteeAllocationController {

    private final GuaranteeContractService contractService;

    public GuaranteeAllocationController(GuaranteeContractService contractService) {
        this.contractService = contractService;
    }

    @PostMapping("/{allocationId}/contract")
    public R<Map<String, Object>> createContract(@PathVariable long allocationId,
                                                 @RequestBody GuaranteeContractService.AllocationContractCmd cmd) {
        return R.ok(contractService.createFromAllocation(allocationId, cmd));
    }
}
