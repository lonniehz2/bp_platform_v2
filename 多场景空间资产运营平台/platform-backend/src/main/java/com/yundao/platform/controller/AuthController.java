package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.common.auth.UserContext;
import com.yundao.platform.service.AuthService;
import com.yundao.platform.service.MenuService;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/auth")
public class AuthController {

    private final AuthService authService;
    private final MenuService menuService;
    private final com.yundao.platform.service.PermissionService permissionService;

    public AuthController(AuthService authService,
                          com.yundao.platform.service.PermissionService permissionService,
                          MenuService menuService) {
        this.authService = authService;
        this.permissionService = permissionService;
        this.menuService = menuService;
    }

    @PostMapping("/login")
    public R<AuthService.LoginResult> login(@RequestBody AuthService.LoginCmd cmd) {
        return R.ok(authService.login(cmd));
    }

    @GetMapping("/permissions")
    public R<java.util.List<String>> permissions() {
        return R.ok(java.util.List.copyOf(permissionService.permissions()));
    }

    @GetMapping("/menu-tree")
    public R<java.util.List<java.util.Map<String, Object>>> menuTree(@org.springframework.web.bind.annotation.RequestParam(defaultValue = "GUARANTEE") String sceneCode) {
        com.yundao.platform.common.auth.UserContext.Principal p = UserContext.require();
        return R.ok(menuService.userMenuTree(p.userId(), p.tenantId(), sceneCode));
    }

    @GetMapping("/menus")
    public R<java.util.List<String>> menus(@org.springframework.web.bind.annotation.RequestParam(defaultValue = "GUARANTEE") String sceneCode) {
        UserContext.Principal principal = authService.me();
        return R.ok(authService.menuCodes(principal.userId(), principal.tenantId(), sceneCode));
    }

    @PostMapping("/password")
    public R<Void> changePassword(@RequestBody AuthService.ChangePasswordCmd cmd) {
        authService.changePassword(cmd);
        return R.ok(null);
    }

    @GetMapping("/me")
    public R<Map<String, Object>> me() {
        UserContext.Principal principal = authService.me();
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("userId", principal.userId());
        out.put("tenantId", principal.tenantId());
        out.put("username", principal.username());
        out.put("displayName", principal.displayName());
        out.put("roles", authService.roles(principal.userId(), principal.tenantId()));
        return R.ok(out);
    }
}
