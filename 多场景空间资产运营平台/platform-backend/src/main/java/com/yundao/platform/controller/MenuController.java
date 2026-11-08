package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.MenuService;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/platform")
public class MenuController {

    private final MenuService service;

    public MenuController(MenuService service) {
        this.service = service;
    }

    @GetMapping("/menus")
    public R<List<Map<String, Object>>> menus(@RequestParam String sceneCode) {
        return R.ok(service.menuTree(sceneCode));
    }

    @GetMapping("/roles")
    public R<List<Map<String, Object>>> roles(@RequestParam String sceneCode) {
        return R.ok(service.roles(sceneCode));
    }

    @GetMapping("/roles/{roleId}/menus")
    public R<List<Map<String, Object>>> roleMenus(@PathVariable long roleId) {
        return R.ok(service.roleMenus(roleId));
    }

    @PostMapping("/roles")
    public R<Map<String, Object>> createRole(@RequestBody MenuService.CreateRoleCmd cmd) {
        return R.ok(service.createRole(cmd));
    }

    @PostMapping("/roles/{roleId}/menus")
    public R<Map<String, Object>> saveRoleMenus(@PathVariable long roleId,
                                                @RequestBody Map<String, List<String>> body) {
        return R.ok(service.saveMenus(roleId, body.get("menuCodes")));
    }
}
