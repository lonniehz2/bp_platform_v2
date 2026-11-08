package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.common.auth.UserContext;
import com.yundao.platform.service.AuthService;
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

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    @PostMapping("/login")
    public R<AuthService.LoginResult> login(@RequestBody AuthService.LoginCmd cmd) {
        return R.ok(authService.login(cmd));
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
