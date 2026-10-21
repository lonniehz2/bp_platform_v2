package com.yundao.bp.iam.security;

import java.util.Collections;
import java.util.Set;

/**
 * 当前登录用户（线程级）。
 */
public final class LoginUser {

    private static final ThreadLocal<LoginUser> HOLDER = new ThreadLocal<>();

    private final Long userId;
    private final String username;
    private final String realName;
    private final String tenantId;
    private final Long orgId;
    private final boolean admin;
    private final String tokenId;
    private final Set<String> permissions;

    public LoginUser(Long userId, String username, String realName, String tenantId, Long orgId,
                     boolean admin, String tokenId, Set<String> permissions) {
        this.userId = userId;
        this.username = username;
        this.realName = realName;
        this.tenantId = tenantId;
        this.orgId = orgId;
        this.admin = admin;
        this.tokenId = tokenId;
        this.permissions = permissions == null ? Set.of() : permissions;
    }

    public Long userId() {
        return userId;
    }

    public String username() {
        return username;
    }

    public String realName() {
        return realName;
    }

    public String tenantId() {
        return tenantId;
    }

    public Long orgId() {
        return orgId;
    }

    public boolean admin() {
        return admin;
    }

    public String tokenId() {
        return tokenId;
    }

    public Set<String> permissions() {
        return Collections.unmodifiableSet(permissions);
    }

    /** 是否拥有某权限（管理员放行）。 */
    public boolean has(String permCode) {
        return admin || permissions.contains(permCode);
    }

    public static void set(LoginUser u) {
        HOLDER.set(u);
    }

    public static LoginUser get() {
        return HOLDER.get();
    }

    public static void clear() {
        HOLDER.remove();
    }
}
