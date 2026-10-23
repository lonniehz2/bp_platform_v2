package com.yundao.bp.ops.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.ops.dto.VisitCreateCmd;
import com.yundao.bp.ops.dto.VisitResultCmd;
import com.yundao.bp.ops.dto.VisitVO;
import com.yundao.bp.ops.service.VisitService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 巡房/入户走访接口（BC-06）。
 *
 * <p>保障房"使用情况核查"的落地手段：走访回填 {@code isSublease/isIdle/isIllegalUse}
 * 三个标记，命中后转工单处置。
 */
@RestController
@RequestMapping("/api/v1/visits")
public class VisitController {

    private final VisitService visitService;

    public VisitController(VisitService visitService) {
        this.visitService = visitService;
    }

    @com.yundao.bp.iam.security.RequirePerm("ops:visit:create")
    @PostMapping
    public R<VisitVO> create(@Valid @RequestBody VisitCreateCmd cmd) {
        return R.ok(visitService.create(cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("ops:visit:view")
    @GetMapping("/{id}")
    public R<VisitVO> get(@PathVariable Long id) {
        return R.ok(visitService.get(id));
    }

    @com.yundao.bp.iam.security.RequirePerm("ops:visit:view")
    @GetMapping
    public R<PageResult<VisitVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                       @RequestParam(defaultValue = "20") long pageSize,
                                       @RequestParam(required = false) String visitType,
                                       @RequestParam(required = false) String visitStatus,
                                       @RequestParam(required = false) Long houseId,
                                       @RequestParam(required = false) String keyword) {
        return R.ok(visitService.page(pageNum, pageSize, visitType, visitStatus, houseId, keyword));
    }

    /** 回填走访结果。 */
    @com.yundao.bp.iam.security.RequirePerm("ops:visit:create")
    @PostMapping("/{id}/report")
    public R<VisitVO> report(@PathVariable Long id, @Valid @RequestBody VisitResultCmd cmd) {
        return R.ok(visitService.report(id, cmd));
    }

    /** 走访异常转工单。 */
    @com.yundao.bp.iam.security.RequirePerm("ops:visit:create")
    @PostMapping("/{id}/to-workorder")
    public R<VisitVO> toWorkOrder(@PathVariable Long id,
                                  @RequestBody(required = false) Cmd cmd) {
        return R.ok(visitService.toWorkOrder(id,
                cmd == null ? null : cmd.operatorId(),
                cmd == null ? null : cmd.operatorName()));
    }

    @com.yundao.bp.iam.security.RequirePerm("ops:visit:cancel")
    @PostMapping("/{id}/cancel")
    public R<VisitVO> cancel(@PathVariable Long id, @RequestBody(required = false) Cmd cmd) {
        return R.ok(visitService.cancel(id, cmd == null ? null : cmd.reason()));
    }

    public record Cmd(Long operatorId, String operatorName, String reason) {
    }
}
