package com.yundao.platform.common.auth;

public final class UserContext {

    private static final ThreadLocal<Principal> CURRENT = new ThreadLocal<>();

    private UserContext() {
    }

    public static void set(Principal principal) {
        CURRENT.set(principal);
    }

    public static Principal get() {
        return CURRENT.get();
    }

    public static Principal require() {
        Principal principal = CURRENT.get();
        if (principal == null) {
            throw new IllegalStateException("缺少登录上下文");
        }
        return principal;
    }

    public static void clear() {
        CURRENT.remove();
    }

    public record Principal(long userId, String tenantId, String username, String displayName) {
    }
}
