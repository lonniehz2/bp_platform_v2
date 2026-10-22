package com.yundao.bp.fin.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.fin.dto.ArrearsActionCreateCmd;
import com.yundao.bp.fin.dto.ArrearsActionVO;
import com.yundao.bp.fin.service.ArrearsActionService;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 欠费停权处置接口（BC-08）。
 *
 * <p>⭐ <b>安全底线</b>：冻结默认保留大门门禁（{@code EXCLUDE_MAIN_DOOR}）；
 * 使用 {@code ALL} 停用大门须显式确认风险。
 */
@RestController
@RequestMapping("/api/v1/fin/arrears")
public class ArrearsActionController {

    private final ArrearsActionService service;

    public ArrearsActionController(ArrearsActionService service) {
        this.service = service;
    }

    /** 欠费扫描（只给建议，不落库）。 */
    @com.yundao.bp.iam.security.RequirePerm("fin:arrear:view")
    @GetMapping("/scan")
    public R<List<ArrearsActionService.ArrearsSuggestion>> scan(
            @RequestParam(defaultValue = "1") int minOverdueDays) {
        return R.ok(service.scanArrears(minOverdueDays));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:arrear:create")
    @PostMapping
    public R<ArrearsActionVO> create(@Valid @RequestBody ArrearsActionCreateCmd cmd) {
        return R.ok(service.create(cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:arrear:view")
    @GetMapping("/{id}")
    public R<ArrearsActionVO> get(@PathVariable Long id) {
        return R.ok(service.get(id));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:arrear:view")
    @GetMapping
    public R<PageResult<ArrearsActionVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                               @RequestParam(defaultValue = "20") long pageSize,
                                               @RequestParam(required = false) Long contractId,
                                               @RequestParam(required = false) Long personId,
                                               @RequestParam(required = false) String actionType,
                                               @RequestParam(required = false) String status) {
        return R.ok(service.page(pageNum, pageSize, contractId, personId, actionType, status));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:arrear:view")
    @GetMapping("/by-contract/{contractId}")
    public R<List<ArrearsActionVO>> byContract(@PathVariable Long contractId) {
        return R.ok(service.listByContract(contractId));
    }

    /** 执行处置。 */
    @com.yundao.bp.iam.security.RequirePerm("fin:arrear:view")
    @PostMapping("/{id}/execute")
    public R<ArrearsActionVO> execute(@PathVariable Long id) {
        return R.ok(service.execute(id));
    }

    /** 撤销处置（已缴清）。 */
    @com.yundao.bp.iam.security.RequirePerm("fin:arrear:view")
    @PostMapping("/{id}/revoke")
    public R<ArrearsActionVO> revoke(@PathVariable Long id,
                                     @RequestBody(required = false) ReasonCmd cmd) {
        return R.ok(service.revoke(id, cmd == null ? null : cmd.reason()));
    }

    public record ReasonCmd(String reason) {
    }
}
