package com.yundao.bp.iam.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.iam.dto.OrgCreateCmd;
import com.yundao.bp.iam.dto.OrgVO;
import com.yundao.bp.iam.service.OrgService;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 组织管理接口（BC-01）。
 *
 * <p>租户由请求头 {@code X-Tenant-Id} 指定（开发阶段），生产改为 JWT。
 */
@RestController
@RequestMapping("/api/v1/orgs")
public class OrgController {

    private final OrgService orgService;

    public OrgController(OrgService orgService) {
        this.orgService = orgService;
    }

    @com.yundao.bp.iam.security.RequirePerm("orgs:orgs:create")
    @PostMapping
    public R<OrgVO> create(@Valid @RequestBody OrgCreateCmd cmd) {
        return R.ok(orgService.create(cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("orgs:orgs:view")
    @GetMapping("/{id}")
    public R<OrgVO> get(@PathVariable Long id) {
        return R.ok(orgService.get(id));
    }

    @com.yundao.bp.iam.security.RequirePerm("orgs:orgs:view")
    @GetMapping
    public R<PageResult<OrgVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                    @RequestParam(defaultValue = "20") long pageSize,
                                    @RequestParam(required = false) String keyword,
                                    @RequestParam(required = false) Long parentId,
                                    @RequestParam(required = false) Boolean includeSubtree) {
        return R.ok(orgService.page(pageNum, pageSize, keyword, parentId, includeSubtree));
    }

    @com.yundao.bp.iam.security.RequirePerm("orgs:children:view")
    @GetMapping("/children")
    public R<List<OrgVO>> children(@RequestParam(required = false) Long parentId) {
        return R.ok(orgService.children(parentId));
    }


    @com.yundao.bp.iam.security.RequirePerm("orgs:orgs:update")
    @PutMapping("/{id}")
    public R<OrgVO> update(@PathVariable Long id, @Valid @RequestBody OrgCreateCmd cmd) {
        return R.ok(orgService.update(id, cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("orgs:orgs:update")
    @PostMapping("/{id}/status")
    public R<OrgVO> changeStatus(@PathVariable Long id, @RequestBody java.util.Map<String, String> body) {
        return R.ok(orgService.changeStatus(id, body == null ? null : body.get("status")));
    }

    @com.yundao.bp.iam.security.RequirePerm("orgs:orgs:delete")
    @DeleteMapping("/{id}")
    public R<Void> delete(@PathVariable Long id) {
        orgService.delete(id);
        return R.ok();
    }
}
