package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.MenuService;
import com.yundao.platform.service.RoleScopeService;
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
    private final RoleScopeService roleScopeService;

    public MenuController(MenuService service, RoleScopeService roleScopeService) {
        this.service = service;
        this.roleScopeService = roleScopeService;
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

    @GetMapping("/roles/{roleId}/scope")
    public R<Map<String, Object>> roleScope(@PathVariable long roleId) {
        return R.ok(roleScopeService.get(roleId));
    }

    @PostMapping("/roles/{roleId}/scope")
    public R<Map<String, Object>> saveRoleScope(@PathVariable long roleId,
                                                @RequestBody RoleScopeService.ScopeCmd cmd) {
        return R.ok(roleScopeService.save(roleId, cmd));
    }

    @GetMapping("/roles/{roleId}/actions")
    public R<Map<String, Object>> roleActions(@PathVariable long roleId) {
        return R.ok(roleScopeService.actions(roleId));
    }

    @PostMapping("/roles/{roleId}/actions")
    public R<Map<String, Object>> saveRoleActions(@PathVariable long roleId,
                                                  @RequestBody Map<String, List<String>> body) {
        return R.ok(roleScopeService.saveActions(roleId, body.get("actions")));
    }

    @GetMapping("/roles/{roleId}/members")
    public R<List<Map<String, Object>>> roleMembers(@PathVariable long roleId) {
        return R.ok(service.roleMembers(roleId));
    }

    @PostMapping("/roles/{roleId}/update")
    public R<Map<String, Object>> updateRole(@PathVariable long roleId,
                                             @RequestBody MenuService.UpdateRoleCmd cmd) {
        return R.ok(service.updateRole(roleId, cmd));
    }

    @PostMapping("/roles/{roleId}/delete")
    public R<Map<String, Object>> deleteRole(@PathVariable long roleId) {
        return R.ok(service.deleteRole(roleId));
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
