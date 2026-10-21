# -*- coding: utf-8 -*-
"""生成 RBAC：权限拦截器 + 认证/管理接口 + 初始化数据"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
F = {}

# ==================== 拦截器 ====================
F['iam/security/AuthInterceptor.java'] = '''package com.yundao.bp.iam.security;

import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.api.R;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
import com.yundao.bp.iam.service.AuthService;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.method.HandlerMethod;
import org.springframework.web.servlet.HandlerInterceptor;

/**
 * 认证与鉴权拦截器。
 *
 * <p><b>职责</b>：
 * <ol>
 *   <li>校验 `Authorization: Bearer &lt;token&gt;`（或 `X-Token`）</li>
 *   <li>加载会话 → 写入 {@link LoginUser} 与租户上下文</li>
 *   <li>若接口标注 {@link RequirePerm}，校验权限</li>
 * </ol>
 *
 * <p><b>放行白名单</b>：登录接口、健康检查、静态资源。
 *
 * <p><b>演示兼容</b>：当 {@code bp.security.enabled=false} 时退化为
 * 「信任 X-Tenant-Id / X-User-Id 请求头」的开发模式（**仅限本地演示**）。
 */
@Component
public class AuthInterceptor implements HandlerInterceptor {

    private static final Logger log = LoggerFactory.getLogger(AuthInterceptor.class);
    private static final ObjectMapper JSON = new ObjectMapper();

    private final AuthService authService;
    private final boolean securityEnabled;

    public AuthInterceptor(AuthService authService,
                           @Value("${bp.security.enabled:true}") boolean securityEnabled) {
        this.authService = authService;
        this.securityEnabled = securityEnabled;
        log.info("认证拦截器已启用，security.enabled={}", securityEnabled);
    }

    @Override
    public boolean preHandle(HttpServletRequest req, HttpServletResponse resp, Object handler)
            throws Exception {
        // 放行：预检请求
        if ("OPTIONS".equalsIgnoreCase(req.getMethod())) {
            return true;
        }
        String path = req.getRequestURI();
        // 放行：登录、健康检查
        if (path.startsWith("/api/v1/auth/login") || path.startsWith("/actuator/")
                || path.equals("/") || path.startsWith("/index.html")
                || path.startsWith("/favicon") || path.startsWith("/error")) {
            return true;
        }

        // 非 API 请求不影响（静态资源）
        if (!path.startsWith("/api/")) {
            return true;
        }

        // 开发模式：信任请求头（仅本地演示，生产必须关闭 bp.security.enabled）
        if (!securityEnabled) {
            String tid = req.getHeader("X-Tenant-Id");
            String uid = req.getHeader("X-User-Id");
            if (tid != null && !tid.isBlank()) {
                Long userId = uid == null || uid.isBlank() ? null : Long.valueOf(uid);
                TenantContext.set(TenantInfo.of(tid, userId));
                LoginUser.set(new LoginUser(userId, "dev", "开发模式", tid, null, true,
                        "dev-token", java.util.Set.of("*")));
            }
            return true;
        }

        String token = extractToken(req);
        LoginUser user = authService.loadByToken(token);
        if (user == null) {
            reject(resp, 401, ErrorCode.TENANT_CONTEXT_MISSING,
                    "未登录或登录已过期，请重新登录");
            return false;
        }

        // 租户上下文（多租户隔离必需）
        TenantContext.set(TenantInfo.of(user.tenantId(), user.userId()));
        LoginUser.set(user);

        // 权限校验
        RequirePerm perm = resolvePerm(handler);
        if (perm != null && !user.has(perm.value())) {
            log.warn("权限不足：user={} 需要={} 路径={}", user.username(), perm.value(), path);
            reject(resp, 403, ErrorCode.PARAM_INVALID,
                    "无操作权限（需要权限：" + perm.value() + "）");
            return false;
        }
        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest req, HttpServletResponse resp, Object handler,
                                Exception ex) {
        TenantContext.clear();
        LoginUser.clear();
    }

    /** 方法级优先，其次类级。 */
    private static RequirePerm resolvePerm(Object handler) {
        if (!(handler instanceof HandlerMethod hm)) {
            return null;
        }
        RequirePerm m = hm.getMethodAnnotation(RequirePerm.class);
        if (m != null) {
            return m;
        }
        return hm.getBeanType().getAnnotation(RequirePerm.class);
    }

    private static String extractToken(HttpServletRequest req) {
        String auth = req.getHeader("Authorization");
        if (auth != null && auth.startsWith("Bearer ")) {
            return auth.substring(7).trim();
        }
        String t = req.getHeader("X-Token");
        return t == null ? null : t.trim();
    }

    private static void reject(HttpServletResponse resp, int httpStatus, ErrorCode code,
                               String msg) throws Exception {
        resp.setStatus(httpStatus);
        resp.setContentType("application/json;charset=UTF-8");
        R<Void> body = new R<>(code.getCode(), msg, null, System.currentTimeMillis());
        resp.getOutputStream().write(
                JSON.writeValueAsString(body).getBytes(StandardCharsets.UTF_8));
    }
}
'''

# ==================== 注册拦截器 ====================
F['iam/security/WebSecurityConfig.java'] = '''package com.yundao.bp.iam.security;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * 拦截器注册：对所有 `/api/**` 生效。
 */
@Configuration
public class WebSecurityConfig implements WebMvcConfigurer {

    private final AuthInterceptor authInterceptor;

    public WebSecurityConfig(AuthInterceptor authInterceptor) {
        this.authInterceptor = authInterceptor;
    }

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(authInterceptor)
                .addPathPatterns("/api/**")
                .order(0);
    }
}
'''

# ==================== 认证 Controller ====================
F['iam/controller/AuthController.java'] = '''package com.yundao.bp.iam.controller;

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
    @PostMapping("/login")
    public R<LoginVO> login(@Valid @RequestBody LoginCmd cmd, HttpServletRequest req) {
        return R.ok(authService.login(cmd, clientIp(req)));
    }

    /** 登出。 */
    @PostMapping("/logout")
    public R<Void> logout(HttpServletRequest req) {
        authService.logout(token(req));
        return R.ok(null);
    }

    /** 当前用户（含权限清单，供前端控制菜单/按钮）。 */
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
'''

# ==================== 管理 Controller ====================
F['iam/controller/RbacController.java'] = '''package com.yundao.bp.iam.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.api.R;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.iam.entity.IamPermission;
import com.yundao.bp.iam.entity.IamRole;
import com.yundao.bp.iam.entity.IamRolePermission;
import com.yundao.bp.iam.entity.IamUser;
import com.yundao.bp.iam.entity.IamUserRole;
import com.yundao.bp.iam.mapper.IamPermissionMapper;
import com.yundao.bp.iam.mapper.IamRoleMapper;
import com.yundao.bp.iam.mapper.IamRolePermissionMapper;
import com.yundao.bp.iam.mapper.IamUserMapper;
import com.yundao.bp.iam.mapper.IamUserRoleMapper;
import com.yundao.bp.iam.security.PasswordHasher;
import com.yundao.bp.iam.security.RequirePerm;
import java.time.LocalDateTime;
import java.util.List;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 用户 / 角色 / 权限管理接口。
 *
 * <p>全部标注 {@link RequirePerm}，仅具备对应权限的账号可操作。
 */
@RestController
@RequestMapping("/api/v1/rbac")
public class RbacController {

    private final IamUserMapper userMapper;
    private final IamRoleMapper roleMapper;
    private final IamPermissionMapper permMapper;
    private final IamUserRoleMapper userRoleMapper;
    private final IamRolePermissionMapper rolePermMapper;
    private final PasswordHasher hasher;
    private final SnowflakeIdGenerator idGen;

    public RbacController(IamUserMapper userMapper, IamRoleMapper roleMapper,
                          IamPermissionMapper permMapper, IamUserRoleMapper userRoleMapper,
                          IamRolePermissionMapper rolePermMapper, PasswordHasher hasher,
                          SnowflakeIdGenerator idGen) {
        this.userMapper = userMapper;
        this.roleMapper = roleMapper;
        this.permMapper = permMapper;
        this.userRoleMapper = userRoleMapper;
        this.rolePermMapper = rolePermMapper;
        this.hasher = hasher;
        this.idGen = idGen;
    }

    // ---------- 用户 ----------

    @PostMapping("/users")
    @RequirePerm("iam:user:create")
    @Transactional(rollbackFor = Exception.class)
    public R<IamUser> createUser(@RequestBody UserCmd cmd) {
        if (cmd.username() == null || cmd.username().isBlank()) {
            throw BizException.paramInvalid("登录名不能为空");
        }
        Long dup = userMapper.selectCount(new LambdaQueryWrapper<IamUser>()
                .eq(IamUser::getUsername, cmd.username()));
        if (dup != null && dup > 0) {
            throw new BizException(com.yundao.bp.common.api.ErrorCode.DUPLICATED,
                    "登录名已存在");
        }
        long id = idGen.nextId();
        IamUser u = new IamUser();
        u.setId(id);
        u.setTenantId(TenantContext.tenantId());
        u.setUsername(cmd.username());
        u.setPasswordHash(hasher.hash(cmd.password() == null ? "123456" : cmd.password()));
        u.setRealName(cmd.realName());
        u.setOrgId(cmd.orgId());
        u.setUserType(cmd.userType() == null ? "STAFF" : cmd.userType());
        u.setIsAdmin(0);
        u.setSingleDevice(0);
        u.setLoginCount(0);
        u.setStatus("ENABLED");
        u.setIsDeleted(0);
        u.setCreateTime(LocalDateTime.now());
        u.setUpdateTime(LocalDateTime.now());
        userMapper.insert(u);
        u.setPasswordHash(null);
        return R.ok(u);
    }

    @GetMapping("/users")
    @RequirePerm("iam:user:list")
    public R<List<IamUser>> listUsers() {
        List<IamUser> list = userMapper.selectList(null);
        list.forEach(u -> u.setPasswordHash(null));
        return R.ok(list);
    }

    /** 给用户分配角色。 */
    @PostMapping("/users/{userId}/roles")
    @RequirePerm("iam:user:assign")
    @Transactional(rollbackFor = Exception.class)
    public R<Integer> assignRoles(@PathVariable Long userId, @RequestBody IdsCmd cmd) {
        userRoleMapper.delete(new LambdaQueryWrapper<IamUserRole>()
                .eq(IamUserRole::getUserId, userId));
        int n = 0;
        for (Long rid : cmd.ids()) {
            IamUserRole ur = new IamUserRole();
            ur.setId(idGen.nextId());
            ur.setTenantId(TenantContext.tenantId());
            ur.setUserId(userId);
            ur.setRoleId(rid);
            ur.setCreateTime(LocalDateTime.now());
            userRoleMapper.insert(ur);
            n++;
        }
        return R.ok(n);
    }

    // ---------- 角色 ----------

    @PostMapping("/roles")
    @RequirePerm("iam:role:create")
    @Transactional(rollbackFor = Exception.class)
    public R<IamRole> createRole(@RequestBody RoleCmd cmd) {
        Long dup = roleMapper.selectCount(new LambdaQueryWrapper<IamRole>()
                .eq(IamRole::getRoleCode, cmd.roleCode()));
        if (dup != null && dup > 0) {
            throw new BizException(com.yundao.bp.common.api.ErrorCode.DUPLICATED,
                    "角色编码已存在");
        }
        long id = idGen.nextId();
        IamRole r = new IamRole();
        r.setId(id);
        r.setTenantId(TenantContext.tenantId());
        r.setRoleCode(cmd.roleCode());
        r.setRoleName(cmd.roleName());
        r.setRoleType("CUSTOM");
        r.setDataScope(cmd.dataScope() == null ? "ORG" : cmd.dataScope());
        r.setSortNo(0);
        r.setStatus("ENABLED");
        r.setIsDeleted(0);
        r.setCreateTime(LocalDateTime.now());
        r.setUpdateTime(LocalDateTime.now());
        roleMapper.insert(r);
        return R.ok(r);
    }

    @GetMapping("/roles")
    @RequirePerm("iam:role:list")
    public R<List<IamRole>> listRoles() {
        return R.ok(roleMapper.selectList(null));
    }

    /** 给角色分配权限。 */
    @PostMapping("/roles/{roleId}/permissions")
    @RequirePerm("iam:role:assign")
    @Transactional(rollbackFor = Exception.class)
    public R<Integer> assignPermissions(@PathVariable Long roleId, @RequestBody IdsCmd cmd) {
        rolePermMapper.delete(new LambdaQueryWrapper<IamRolePermission>()
                .eq(IamRolePermission::getRoleId, roleId));
        int n = 0;
        for (Long pid : cmd.ids()) {
            IamRolePermission rp = new IamRolePermission();
            rp.setId(idGen.nextId());
            rp.setTenantId(TenantContext.tenantId());
            rp.setRoleId(roleId);
            rp.setPermissionId(pid);
            rp.setCreateTime(LocalDateTime.now());
            rolePermMapper.insert(rp);
            n++;
        }
        return R.ok(n);
    }

    // ---------- 权限 ----------

    @PostMapping("/permissions")
    @RequirePerm("iam:perm:create")
    @Transactional(rollbackFor = Exception.class)
    public R<IamPermission> createPermission(@RequestBody PermCmd cmd) {
        Long dup = permMapper.selectCount(new LambdaQueryWrapper<IamPermission>()
                .eq(IamPermission::getPermCode, cmd.permCode()));
        if (dup != null && dup > 0) {
            throw new BizException(com.yundao.bp.common.api.ErrorCode.DUPLICATED,
                    "权限标识已存在");
        }
        long id = idGen.nextId();
        IamPermission p = new IamPermission();
        p.setId(id);
        p.setParentId(cmd.parentId());
        p.setPermCode(cmd.permCode());
        p.setPermName(cmd.permName());
        p.setPermType(cmd.permType() == null ? "API" : cmd.permType());
        p.setRoutePath(cmd.routePath());
        p.setScenario(cmd.scenario());
        p.setSortNo(cmd.sortNo() == null ? 0 : cmd.sortNo());
        p.setStatus("ENABLED");
        p.setCreateTime(LocalDateTime.now());
        permMapper.insert(p);
        return R.ok(p);
    }

    @GetMapping("/permissions")
    public R<List<IamPermission>> listPermissions() {
        return R.ok(permMapper.selectList(new LambdaQueryWrapper<IamPermission>()
                .orderByAsc(IamPermission::getSortNo)));
    }

    // ---------- 请求体 ----------

    public record UserCmd(String username, String password, String realName, Long orgId,
                          String userType) {
    }

    public record RoleCmd(String roleCode, String roleName, String dataScope) {
    }

    public record PermCmd(Long parentId, String permCode, String permName, String permType,
                          String routePath, String scenario, Integer sortNo) {
    }

    public record IdsCmd(List<Long> ids) {
    }
}
'''

count = 0
for rel, content in F.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个文件' % count)
