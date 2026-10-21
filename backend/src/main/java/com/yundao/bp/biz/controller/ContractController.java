package com.yundao.bp.biz.controller;

import com.yundao.bp.biz.dto.ContractCreateCmd;
import com.yundao.bp.biz.dto.ContractVO;
import com.yundao.bp.biz.service.ContractService;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import jakarta.validation.Valid;
import java.math.BigDecimal;
import java.time.LocalDate;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 合同接口（BC-05 业务办理）。
 *
 * <p>生命周期：起草 → 提交签约 → 发起签署 → 签署生效 →（续签 / 到期 / 终止）。
 */
@RestController
@RequestMapping("/api/v1/contracts")
public class ContractController {

    private final ContractService contractService;

    public ContractController(ContractService contractService) {
        this.contractService = contractService;
    }

    @PostMapping
    public R<ContractVO> create(@Valid @RequestBody ContractCreateCmd cmd) {
        return R.ok(contractService.create(cmd));
    }

    @GetMapping("/{id}")
    public R<ContractVO> get(@PathVariable Long id) {
        return R.ok(contractService.get(id));
    }

    @GetMapping
    public R<PageResult<ContractVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                          @RequestParam(defaultValue = "20") long pageSize,
                                          @RequestParam(required = false) String contractType,
                                          @RequestParam(required = false) String status,
                                          @RequestParam(required = false) Long houseId,
                                          @RequestParam(required = false) Long lesseePersonId,
                                          @RequestParam(required = false) String keyword) {
        return R.ok(contractService.page(pageNum, pageSize, contractType, status, houseId,
                lesseePersonId, keyword));
    }

    @PostMapping("/{id}/submit-sign")
    public R<ContractVO> submitSign(@PathVariable Long id) {
        return R.ok(contractService.submitSign(id));
    }

    @PostMapping("/{id}/start-signing")
    public R<ContractVO> startSigning(@PathVariable Long id,
                                      @RequestBody(required = false) SignCmd cmd) {
        return R.ok(contractService.startSigning(id, cmd == null ? null : cmd.signVendor()));
    }

    /** 签署生效。 */
    @PostMapping("/{id}/sign")
    public R<ContractVO> sign(@PathVariable Long id, @RequestBody(required = false) SignCmd cmd) {
        return R.ok(contractService.sign(id,
                cmd == null ? null : cmd.signFileUrl(),
                cmd == null ? null : cmd.signFlowId()));
    }

    /** 续签。 */
    @PostMapping("/{id}/renew")
    public R<ContractVO> renew(@PathVariable Long id, @RequestBody RenewCmd cmd) {
        return R.ok(contractService.renew(id, cmd.newLeaseEnd(), cmd.newMonthlyRent()));
    }

    /** 终止（退租）。 */
    @PostMapping("/{id}/terminate")
    public R<ContractVO> terminate(@PathVariable Long id,
                                   @RequestBody(required = false) SignCmd cmd) {
        return R.ok(contractService.terminate(id, cmd == null ? null : cmd.reason()));
    }

    @PostMapping("/{id}/cancel")
    public R<ContractVO> cancel(@PathVariable Long id,
                                @RequestBody(required = false) SignCmd cmd) {
        return R.ok(contractService.cancel(id, cmd == null ? null : cmd.reason()));
    }

    /** 到期扫描（可挂定时任务）。 */
    @PostMapping("/expire-due")
    public R<Integer> expireDue() {
        return R.ok(contractService.expireDue());
    }

    public record SignCmd(String signVendor, String signFileUrl, String signFlowId, String reason) {
    }

    public record RenewCmd(
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate newLeaseEnd,
            BigDecimal newMonthlyRent) {
    }
}
