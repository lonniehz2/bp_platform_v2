package com.yundao.bp.grant.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.grant.dto.GrantApplyCmd;
import com.yundao.bp.grant.dto.GrantTaskVO;
import com.yundao.bp.grant.dto.GrantVO;
import com.yundao.bp.grant.entity.GrantTaskDetail;
import com.yundao.bp.grant.service.GrantService;
import com.yundao.bp.grant.service.impl.GrantServiceImpl;
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
 * 授权编排接口（BC-04 权益与钥匙）。
 *
 * <p>授权是<b>异步</b>的：POST 返回时任务通常还是 `PENDING`，
 * 需通过 {@code /tasks/{id}} 轮询下发结果。
 */
@RestController
@RequestMapping("/api/v1/grants")
public class GrantController {

    private final GrantService grantService;
    private final GrantServiceImpl grantServiceImpl;

    public GrantController(GrantService grantService, GrantServiceImpl grantServiceImpl) {
        this.grantService = grantService;
        this.grantServiceImpl = grantServiceImpl;
    }

    @PostMapping
    public R<GrantVO> apply(@Valid @RequestBody GrantApplyCmd cmd) {
        return R.ok(grantService.apply(cmd));
    }

    @GetMapping("/{id}")
    public R<GrantVO> get(@PathVariable Long id) {
        return R.ok(grantService.get(id));
    }

    @GetMapping
    public R<PageResult<GrantVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                       @RequestParam(defaultValue = "20") long pageSize,
                                       @RequestParam(required = false) Long personId,
                                       @RequestParam(required = false) Long spaceId,
                                       @RequestParam(required = false) String grantStatus) {
        return R.ok(grantService.page(pageNum, pageSize, personId, spaceId, grantStatus));
    }

    /** 任务状态（轮询用）。 */
    @GetMapping("/tasks/{taskId}")
    public R<GrantTaskVO> task(@PathVariable Long taskId) {
        return R.ok(grantService.task(taskId));
    }

    /** 任务逐设备明细。 */
    @GetMapping("/tasks/{taskId}/details")
    public R<List<GrantTaskDetail>> details(@PathVariable Long taskId) {
        return R.ok(grantServiceImpl.details(taskId));
    }

    @PostMapping("/{id}/revoke")
    public R<GrantVO> revoke(@PathVariable Long id, @RequestBody(required = false) RevokeCmd cmd) {
        return R.ok(grantService.revoke(id, cmd == null ? null : cmd.reason()));
    }

    public record RevokeCmd(String reason) {
    }
}
