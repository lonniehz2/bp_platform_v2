package com.yundao.bp.ops.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.ops.dto.WorkOrderCreateCmd;
import com.yundao.bp.ops.dto.WorkOrderVO;
import com.yundao.bp.ops.entity.OpsWorkorderLog;
import com.yundao.bp.ops.service.WorkOrderService;
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
 * 工单接口（BC-06 运维告警）。
 *
 * <p>完整闭环：创建 → 派单 → 接单 → 开始 → 完工 → 闭环；每步都有流转记录。
 */
@RestController
@RequestMapping("/api/v1/workorders")
public class WorkOrderController {

    private final WorkOrderService workOrderService;

    public WorkOrderController(WorkOrderService workOrderService) {
        this.workOrderService = workOrderService;
    }

    @PostMapping
    public R<WorkOrderVO> create(@Valid @RequestBody WorkOrderCreateCmd cmd) {
        return R.ok(workOrderService.create(cmd));
    }

    @GetMapping("/{id}")
    public R<WorkOrderVO> get(@PathVariable Long id) {
        return R.ok(workOrderService.get(id));
    }

    @GetMapping("/{id}/logs")
    public R<List<OpsWorkorderLog>> logs(@PathVariable Long id) {
        return R.ok(workOrderService.logs(id));
    }

    @GetMapping
    public R<PageResult<WorkOrderVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                           @RequestParam(defaultValue = "20") long pageSize,
                                           @RequestParam(required = false) String orderType,
                                           @RequestParam(required = false) String orderStatus,
                                           @RequestParam(required = false) Long assignUserId,
                                           @RequestParam(required = false) String keyword) {
        return R.ok(workOrderService.page(pageNum, pageSize, orderType, orderStatus,
                assignUserId, keyword));
    }

    @PostMapping("/{id}/assign")
    public R<WorkOrderVO> assign(@PathVariable Long id, @RequestBody AssignCmd cmd) {
        return R.ok(workOrderService.assign(id, cmd.assignUserId(), cmd.assignUserName(),
                cmd.assignUserPhone(), cmd.content()));
    }

    @PostMapping("/{id}/accept")
    public R<WorkOrderVO> accept(@PathVariable Long id, @RequestBody ActionCmd cmd) {
        return R.ok(workOrderService.accept(id, cmd.operatorId(), cmd.operatorName(),
                cmd.content()));
    }

    @PostMapping("/{id}/start")
    public R<WorkOrderVO> start(@PathVariable Long id, @RequestBody ActionCmd cmd) {
        return R.ok(workOrderService.start(id, cmd.operatorId(), cmd.operatorName(),
                cmd.content()));
    }

    @PostMapping("/{id}/finish")
    public R<WorkOrderVO> finish(@PathVariable Long id, @RequestBody ActionCmd cmd) {
        return R.ok(workOrderService.finish(id, cmd.operatorId(), cmd.operatorName(),
                cmd.handleResult(), cmd.content()));
    }

    @PostMapping("/{id}/close")
    public R<WorkOrderVO> close(@PathVariable Long id, @RequestBody ActionCmd cmd) {
        return R.ok(workOrderService.close(id, cmd.operatorId(), cmd.operatorName(),
                cmd.content()));
    }

    @PostMapping("/{id}/cancel")
    public R<WorkOrderVO> cancel(@PathVariable Long id, @RequestBody ActionCmd cmd) {
        return R.ok(workOrderService.cancel(id, cmd.operatorId(), cmd.operatorName(),
                cmd.content()));
    }

    @PostMapping("/{id}/reject")
    public R<WorkOrderVO> reject(@PathVariable Long id, @RequestBody ActionCmd cmd) {
        return R.ok(workOrderService.reject(id, cmd.operatorId(), cmd.operatorName(),
                cmd.content()));
    }

    public record AssignCmd(Long assignUserId, String assignUserName,
                            String assignUserPhone, String content) {
    }

    public record ActionCmd(Long operatorId, String operatorName,
                            String content, String handleResult) {
    }
}
