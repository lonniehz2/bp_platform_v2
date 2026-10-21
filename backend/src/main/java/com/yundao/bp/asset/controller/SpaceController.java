package com.yundao.bp.asset.controller;

import com.yundao.bp.asset.dto.SpaceCreateCmd;
import com.yundao.bp.asset.dto.SpaceVO;
import com.yundao.bp.asset.service.SpaceService;
import com.yundao.bp.common.api.R;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 空间树接口（BC-02）。
 */
@RestController
@RequestMapping("/api/v1/spaces")
public class SpaceController {

    private final SpaceService spaceService;

    public SpaceController(SpaceService spaceService) {
        this.spaceService = spaceService;
    }

    @PostMapping
    public R<SpaceVO> create(@Valid @RequestBody SpaceCreateCmd cmd) {
        return R.ok(spaceService.create(cmd));
    }

    @GetMapping("/{id}")
    public R<SpaceVO> get(@PathVariable Long id) {
        return R.ok(spaceService.get(id));
    }

    @GetMapping("/children")
    public R<List<SpaceVO>> children(@RequestParam(required = false) Long parentId) {
        return R.ok(spaceService.children(parentId));
    }

    /** 整棵子树（按 path_code 前序排序）。 */
    @GetMapping("/{id}/subtree")
    public R<List<SpaceVO>> subtree(@PathVariable Long id) {
        return R.ok(spaceService.subtree(id));
    }

    /** 某组织（小区）下的完整空间树。 */
    @GetMapping("/tree")
    public R<List<SpaceVO>> tree(@RequestParam Long orgId) {
        return R.ok(spaceService.treeOfOrg(orgId));
    }

    @DeleteMapping("/{id}")
    public R<Void> delete(@PathVariable Long id) {
        spaceService.delete(id);
        return R.ok();
    }
}
