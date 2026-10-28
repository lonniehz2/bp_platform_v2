package com.yundao.bp.biz.controller;

import com.yundao.bp.biz.dto.TerminationCreateCmd;
import com.yundao.bp.biz.dto.TerminationVO;
import com.yundao.bp.biz.service.TerminationService;
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
 * 退租/腾退接口（BC-05 业务办理）。
 *
 * <p>办结需四个前置齐备：验房通过 + 结算完成 + 房源已释放 + 授权已回收。
 */
@RestController
@RequestMapping("/api/v1/terminations")
public class TerminationController {

    private final TerminationService service;

    public TerminationController(TerminationService service) {
        this.service = service;
    }

    @com.yundao.bp.iam.security.RequirePerm("biz:termination:create")
    @PostMapping
    public R<TerminationVO> apply(@Valid @RequestBody TerminationCreateCmd cmd) {
        return R.ok(service.apply(cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("biz:termination:view")
    @GetMapping("/{id}")
    public R<TerminationVO> get(@PathVariable Long id) {
        return R.ok(service.get(id));
    }

    @com.yundao.bp.iam.security.RequirePerm("biz:termination:view")
    @GetMapping("/{id}/settle-preview")
    public R<java.util.Map<String, Object>> settlePreview(@PathVariable Long id) {
        return R.ok(service.settlePreview(id));
    }

    @com.yundao.bp.iam.security.RequirePerm("biz:termination:view")
    @GetMapping
    public R<PageResult<TerminationVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                             @RequestParam(defaultValue = "20") long pageSize,
                                             @RequestParam(required = false) String type,
                                             @RequestParam(required = false) String status,
                                             @RequestParam(required = false) Long contractId,
                                             @RequestParam(required = false) Long houseId,
                                             @RequestParam(required = false) String keyword,
                                             @RequestParam(required = false) Long orgId) {
        return R.ok(service.page(pageNum, pageSize, type, status, contractId, houseId, keyword,
                orgId));
    }

    @com.yundao.bp.iam.security.RequirePerm("biz:termination:submit")
    @PostMapping("/{id}/submit")
    public R<TerminationVO> submit(@PathVariable Long id) {
        return R.ok(service.submit(id));
    }

    @com.yundao.bp.iam.security.RequirePerm("biz:termination:approve")
    @PostMapping("/{id}/approve")
    public R<TerminationVO> approve(@PathVariable Long id,
                                    @RequestBody(required = false) ReasonCmd cmd) {
        return R.ok(service.approve(id, cmd == null ? null : cmd.reason()));
    }

    @com.yundao.bp.iam.security.RequirePerm("biz:termination:create")
    @PostMapping("/{id}/reject")
    public R<TerminationVO> reject(@PathVariable Long id,
                                   @RequestBody(required = false) ReasonCmd cmd) {
        return R.ok(service.reject(id, cmd == null ? null : cmd.reason()));
    }

    @com.yundao.bp.iam.security.RequirePerm("biz:termination:cancel")
    @PostMapping("/{id}/cancel")
    public R<TerminationVO> cancel(@PathVariable Long id,
                                   @RequestBody(required = false) ReasonCmd cmd) {
        return R.ok(service.cancel(id, cmd == null ? null : cmd.reason()));
    }

    /** 验房。 */
    @com.yundao.bp.iam.security.RequirePerm("biz:termination:create")
    @PostMapping("/{id}/inspect")
    public R<TerminationVO> inspect(@PathVariable Long id, @RequestBody InspectCmd cmd) {
        return R.ok(service.inspect(id, cmd.inspectStatus(), cmd.inspectResult(),
                cmd.damageAmount(), cmd.inspectImages()));
    }

    /** 结算。 */
    @com.yundao.bp.iam.security.RequirePerm("biz:termination:create")
    @PostMapping("/{id}/settle")
    public R<TerminationVO> settle(@PathVariable Long id, @RequestBody SettleCmd cmd) {
        return R.ok(service.settle(id, cmd.depositRefund(), cmd.arrearsAmount()));
    }

    /** 标记房源已释放 / 授权已回收。 */
    @com.yundao.bp.iam.security.RequirePerm("biz:termination:create")
    @PostMapping("/{id}/mark-released")
    public R<TerminationVO> markReleased(@PathVariable Long id, @RequestBody ReleaseCmd cmd) {
        return R.ok(service.markReleased(id, cmd.houseReleased(), cmd.grantRevoked()));
    }

    /** 办结。 */
    @com.yundao.bp.iam.security.RequirePerm("biz:termination:create")
    @PostMapping("/{id}/complete")
    public R<TerminationVO> complete(@PathVariable Long id,
                                     @RequestBody(required = false) CompleteCmd cmd) {
        return R.ok(service.complete(id, cmd == null ? null : cmd.actualExitDate()));
    }

    /** 登记强制执行/公证/物品处置人。 */
    @com.yundao.bp.iam.security.RequirePerm("biz:termination:create")
    @PostMapping("/{id}/register-enforce")
    public R<TerminationVO> registerEnforce(@PathVariable Long id,
                                            @RequestBody EnforceCmd cmd) {
        return R.ok(service.registerEnforce(id, cmd.enforceApplyDate(), cmd.enforceCourt(),
                cmd.itemHandlerName(), cmd.itemHandlerPhone(), cmd.notaryNo()));
    }

    public record ReasonCmd(String reason) {
    }

    public record InspectCmd(String inspectStatus, String inspectResult,
                             BigDecimal damageAmount, String inspectImages) {
    }

    public record SettleCmd(BigDecimal depositRefund, BigDecimal arrearsAmount) {
    }

    public record ReleaseCmd(Boolean houseReleased, Boolean grantRevoked) {
    }

    public record CompleteCmd(
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate actualExitDate) {
    }

    public record EnforceCmd(
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate enforceApplyDate,
            String enforceCourt, String itemHandlerName, String itemHandlerPhone,
            String notaryNo) {
    }
}
