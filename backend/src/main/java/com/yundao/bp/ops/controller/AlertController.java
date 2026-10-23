package com.yundao.bp.ops.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.ops.dto.AlertCreateCmd;
import com.yundao.bp.ops.dto.AlertStatsVO;
import com.yundao.bp.ops.dto.AlertVO;
import com.yundao.bp.ops.service.AlertService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 告警中心接口（BC-06 运维告警）。
 */
@RestController
@RequestMapping("/api/v1/alerts")
public class AlertController {

    private final AlertService alertService;

    public AlertController(AlertService alertService) {
        this.alertService = alertService;
    }

    @com.yundao.bp.iam.security.RequirePerm("ops:alert:create")
    @PostMapping
    public R<AlertVO> create(@Valid @RequestBody AlertCreateCmd cmd) {
        return R.ok(alertService.create(cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("ops:alert:view")
    @GetMapping("/{id}")
    public R<AlertVO> get(@PathVariable Long id) {
        return R.ok(alertService.get(id));
    }

    @com.yundao.bp.iam.security.RequirePerm("ops:alert:view")
    @GetMapping
    public R<PageResult<AlertVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                       @RequestParam(defaultValue = "20") long pageSize,
                                       @RequestParam(required = false) String category,
                                       @RequestParam(required = false) String level,
                                       @RequestParam(required = false) String status,
                                       @RequestParam(required = false) Long orgId,
                                       @RequestParam(required = false) String keyword) {
        return R.ok(alertService.page(pageNum, pageSize, category, level, status, orgId, keyword));
    }

    /** 大屏统计。 */
    @com.yundao.bp.iam.security.RequirePerm("ops:alert:view")
    @GetMapping("/stats")
    public R<AlertStatsVO> stats(@RequestParam(required = false) Long orgId) {
        return R.ok(alertService.stats(orgId));
    }

    @com.yundao.bp.iam.security.RequirePerm("ops:alert:handle")
    @PostMapping("/{id}/handle")
    public R<AlertVO> handle(@PathVariable Long id, @RequestBody ActionCmd cmd) {
        return R.ok(alertService.handle(id, cmd.handleUserId(), cmd.action(), cmd.result()));
    }

    @com.yundao.bp.iam.security.RequirePerm("ops:alert:create")
    @PostMapping("/{id}/resolve")
    public R<AlertVO> resolve(@PathVariable Long id, @RequestBody ActionCmd cmd) {
        return R.ok(alertService.resolve(id, cmd.handleUserId(), cmd.result()));
    }

    @com.yundao.bp.iam.security.RequirePerm("ops:alert:create")
    @PostMapping("/{id}/ignore")
    public R<AlertVO> ignore(@PathVariable Long id, @RequestBody ActionCmd cmd) {
        return R.ok(alertService.ignore(id, cmd.handleUserId(), cmd.result()));
    }

    @com.yundao.bp.iam.security.RequirePerm("ops:alert:create")
    @PostMapping("/{id}/escalate")
    public R<AlertVO> escalate(@PathVariable Long id, @RequestBody ActionCmd cmd) {
        return R.ok(alertService.escalate(id, cmd.result()));
    }

    /** 告警转工单。 */
    @com.yundao.bp.iam.security.RequirePerm("ops:alert:create")
    @PostMapping("/{id}/to-workorder")
    public R<AlertVO> toWorkOrder(@PathVariable Long id, @RequestBody(required = false) ActionCmd cmd) {
        return R.ok(alertService.toWorkOrder(id,
                cmd == null ? null : cmd.handleUserId(),
                cmd == null ? null : cmd.action()));
    }

    public record ActionCmd(Long handleUserId, String action, String result) {
    }
}
