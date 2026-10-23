package com.yundao.bp.grant.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.grant.entity.GrantReconcileDiff;
import com.yundao.bp.grant.service.ReconcileService;
import com.yundao.bp.iam.security.RequirePerm;
import com.yundao.bp.sys.audit.Audit;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 授权对账接口（★ 级要求：本地与 IoT 授权一致）。
 */
@RestController
@RequestMapping("/api/v1/grant-reconcile")
public class ReconcileController {

    private final ReconcileService service;

    public ReconcileController(ReconcileService service) {
        this.service = service;
    }

    /** ⭐ 执行对账（可指定某台锁）。 */
    @PostMapping("/run")
    @RequirePerm("grant:reconcile:manage")
    @Audit(type = "SECURITY", level = "IMPORTANT", action = "执行授权对账")
    public R<Map<String, Object>> run(@RequestParam(required = false) String lockId) {
        return R.ok(service.reconcile(lockId));
    }

    @com.yundao.bp.iam.security.RequirePerm("asset:grant:view")
    @GetMapping("/diffs")
    public R<PageResult<GrantReconcileDiff>> diffs(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) String lockId,
            @RequestParam(required = false) String diffType,
            @RequestParam(required = false) String handleStatus) {
        return R.ok(service.pageDiffs(pageNum, pageSize, lockId, diffType, handleStatus));
    }

    @com.yundao.bp.iam.security.RequirePerm("asset:grant:view")
    @GetMapping("/diffs/pending")
    public R<List<GrantReconcileDiff>> pending() {
        return R.ok(service.listByHandleStatus("PENDING"));
    }

    /** ⭐ 处置单条差异。 */
    @PostMapping("/diffs/{id}/handle")
    @RequirePerm("grant:reconcile:manage")
    @Audit(type = "SECURITY", level = "IMPORTANT", action = "处置对账差异")
    public R<GrantReconcileDiff> handle(@PathVariable Long id, @RequestBody HandleCmd cmd) {
        return R.ok(service.handle(id, cmd.action(), cmd.remark()));
    }

    /** ⭐ 批量处置。 */
    @PostMapping("/diffs/handle-batch")
    @RequirePerm("grant:reconcile:manage")
    @Audit(type = "SECURITY", level = "IMPORTANT", action = "批量处置对账差异")
    public R<Map<String, Object>> handleBatch(@RequestBody BatchCmd cmd) {
        return R.ok(service.handleBatch(cmd.diffType(), cmd.action(), cmd.remark()));
    }

    /** 未处置差异统计（看板）。 */
    @com.yundao.bp.iam.security.RequirePerm("asset:grant:view")
    @GetMapping("/stats")
    public R<Map<String, Object>> stats() {
        return R.ok(service.stats());
    }

    public record HandleCmd(String action, String remark) {
    }

    public record BatchCmd(String diffType, String action, String remark) {
    }
}
