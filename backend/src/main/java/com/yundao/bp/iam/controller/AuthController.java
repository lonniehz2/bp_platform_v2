package com.yundao.bp.iam.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.iam.dto.LoginCmd;
import com.yundao.bp.iam.dto.LoginVO;
import com.yundao.bp.iam.dto.MeVO;
import com.yundao.bp.iam.security.LoginUser;
import com.yundao.bp.iam.service.AuthService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 认证接口。
 */
@RestController
@RequestMapping("/api/v1/auth")
public class AuthController {

    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    /** 登录（唯一免鉴权接口）。 */
    @com.yundao.bp.iam.security.RequirePerm("auth:auth:create")
    @PostMapping("/login")
    public R<LoginVO> login(@Valid @RequestBody LoginCmd cmd, HttpServletRequest req) {
        return R.ok(authService.login(cmd, clientIp(req)));
    }

    /** 登出。 */
    @com.yundao.bp.iam.security.RequirePerm("auth:auth:create")
    @PostMapping("/logout")
    public R<Void> logout(HttpServletRequest req) {
        authService.logout(token(req));
        return R.ok(null);
    }

    /** 当前用户（含权限清单，供前端控制菜单/按钮）。 */
    @com.yundao.bp.iam.security.RequirePerm("auth:auth:view")
    @GetMapping("/me")
    public R<MeVO> me() {
        LoginUser u = LoginUser.get();
        return R.ok(authService.me(u.userId()));
    }

    private static String token(HttpServletRequest req) {
        String auth = req.getHeader("Authorization");
        if (auth != null && auth.startsWith("Bearer ")) {
            return auth.substring(7).trim();
        }
        return req.getHeader("X-Token");
    }

    private static String clientIp(HttpServletRequest req) {
        String xf = req.getHeader("X-Forwarded-For");
        if (xf != null && !xf.isBlank()) {
            return xf.split(",")[0].trim();
        }
        return req.getRemoteAddr();
    }
}
