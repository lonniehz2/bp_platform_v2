package com.yundao.bp.ops.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.ops.dto.ComplaintCreateCmd;
import com.yundao.bp.ops.dto.ComplaintVO;
import com.yundao.bp.ops.service.ComplaintService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 投诉建议接口（BC-06）。
 */
@RestController
@RequestMapping("/api/v1/complaints")
public class ComplaintController {

    private final ComplaintService complaintService;

    public ComplaintController(ComplaintService complaintService) {
        this.complaintService = complaintService;
    }

    @com.yundao.bp.iam.security.RequirePerm("ops:complaint:create")
    @PostMapping
    public R<ComplaintVO> create(@Valid @RequestBody ComplaintCreateCmd cmd) {
        return R.ok(complaintService.create(cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("ops:complaint:view")
    @GetMapping("/{id}")
    public R<ComplaintVO> get(@PathVariable Long id) {
        return R.ok(complaintService.get(id));
    }

    @com.yundao.bp.iam.security.RequirePerm("ops:complaint:view")
    @GetMapping
    public R<PageResult<ComplaintVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                           @RequestParam(defaultValue = "20") long pageSize,
                                           @RequestParam(required = false) String type,
                                           @RequestParam(required = false) String status,
                                           @RequestParam(required = false) Long orgId,
                                           @RequestParam(required = false) String keyword) {
        return R.ok(complaintService.page(pageNum, pageSize, type, status, orgId, keyword));
    }

    @com.yundao.bp.iam.security.RequirePerm("ops:complaint:handle")
    @PostMapping("/{id}/handle")
    public R<ComplaintVO> handle(@PathVariable Long id, @RequestBody(required = false) Cmd cmd) {
        return R.ok(complaintService.handle(id, cmd == null ? null : cmd.handleUserId()));
    }

    @com.yundao.bp.iam.security.RequirePerm("ops:complaint:create")
    @PostMapping("/{id}/resolve")
    public R<ComplaintVO> resolve(@PathVariable Long id, @RequestBody(required = false) Cmd cmd) {
        return R.ok(complaintService.resolve(id,
                cmd == null ? null : cmd.handleUserId(),
                cmd == null ? null : cmd.result()));
    }

    @com.yundao.bp.iam.security.RequirePerm("ops:complaint:close")
    @PostMapping("/{id}/close")
    public R<ComplaintVO> close(@PathVariable Long id, @RequestBody(required = false) Cmd cmd) {
        return R.ok(complaintService.close(id, cmd == null ? null : cmd.handleUserId()));
    }

    @com.yundao.bp.iam.security.RequirePerm("ops:complaint:create")
    @PostMapping("/{id}/evaluate")
    public R<ComplaintVO> evaluate(@PathVariable Long id, @RequestBody EvalCmd cmd) {
        return R.ok(complaintService.evaluate(id, cmd.satisfaction()));
    }

    @com.yundao.bp.iam.security.RequirePerm("ops:complaint:create")
    @PostMapping("/{id}/to-workorder")
    public R<ComplaintVO> toWorkOrder(@PathVariable Long id,
                                      @RequestBody(required = false) Cmd cmd) {
        return R.ok(complaintService.toWorkOrder(id,
                cmd == null ? null : cmd.handleUserId(),
                cmd == null ? null : cmd.action()));
    }

    public record Cmd(Long handleUserId, String action, String result) {
    }

    public record EvalCmd(Integer satisfaction) {
    }
}
