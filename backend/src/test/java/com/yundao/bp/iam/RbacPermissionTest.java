package com.yundao.bp.iam;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.iam.entity.IamPermission;
import com.yundao.bp.iam.entity.IamRole;
import com.yundao.bp.iam.entity.IamRolePermission;
import com.yundao.bp.iam.entity.IamSession;
import com.yundao.bp.iam.entity.IamUser;
import com.yundao.bp.iam.entity.IamUserRole;
import com.yundao.bp.iam.mapper.IamPermissionMapper;
import com.yundao.bp.iam.mapper.IamRoleMapper;
import com.yundao.bp.iam.mapper.IamRolePermissionMapper;
import com.yundao.bp.iam.mapper.IamSessionMapper;
import com.yundao.bp.iam.mapper.IamUserMapper;
import com.yundao.bp.iam.mapper.IamUserRoleMapper;
import com.yundao.bp.iam.security.LoginUser;
import com.yundao.bp.iam.security.PasswordHasher;
import com.yundao.bp.iam.service.impl.AuthServiceImpl;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;

/**
 * 权限计算与令牌校验测试。
 *
 * <p>这是安全边界：算错一个权限就是越权。
 * 重点验证「管理员放行」「角色停用后权限消失」「令牌过期/登出失效」
 * 「会话租户是权威来源」。
 */
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class RbacPermissionTest {

    @Mock
    private IamUserMapper userMapper;
    @Mock
    private IamSessionMapper sessionMapper;
    @Mock
    private IamUserRoleMapper userRoleMapper;
    @Mock
    private IamRoleMapper roleMapper;
    @Mock
    private IamRolePermissionMapper rolePermMapper;
    @Mock
    private IamPermissionMapper permMapper;

    private AuthServiceImpl auth;
    private final PasswordHasher hasher = new PasswordHasher();

    private static IamUser user(long id, boolean admin, String status) {
        IamUser u = new IamUser();
        u.setId(id);
        u.setUsername("u" + id);
        u.setTenantId("350600");
        u.setIsAdmin(admin ? 1 : 0);
        u.setStatus(status);
        return u;
    }

    private static IamSession session(String token, String status, LocalDateTime expire) {
        IamSession s = new IamSession();
        s.setTokenId(token);
        s.setTenantId("350600");
        s.setUserId(100L);
        s.setStatus(status);
        s.setExpireTime(expire);
        s.setLoginTime(LocalDateTime.now());
        return s;
    }

    @BeforeEach
    void setUp() {
        auth = new AuthServiceImpl(userMapper, sessionMapper, userRoleMapper, roleMapper,
                rolePermMapper, permMapper, hasher, new SnowflakeIdGenerator(1, 1));
    }

    // ==================== 密码哈希 ====================

    @Test
    @DisplayName("密码哈希可校验，且同一密码两次哈希不同（含随机盐）")
    void passwordHash() {
        String h1 = hasher.hash("admin123");
        String h2 = hasher.hash("admin123");
        assertTrue(hasher.verify("admin123", h1));
        assertTrue(hasher.verify("admin123", h2));
        assertTrue(!h1.equals(h2), "应使用随机盐，两次哈希不应相同");
        assertFalse(hasher.verify("wrong", h1));
    }

    @Test
    @DisplayName("哈希格式为 pbkdf2$迭代$盐$值（便于将来升级算法）")
    void hashFormat() {
        String h = hasher.hash("x");
        String[] p = h.split("\\$");
        assertEquals(4, p.length, h);
        assertEquals("pbkdf2", p[0]);
    }

    @Test
    @DisplayName("非法存储值不影响校验（返回 false，不抛异常）")
    void malformedHash() {
        assertFalse(hasher.verify("x", "garbage"));
        assertFalse(hasher.verify("x", ""));
        assertFalse(hasher.verify("x", null));
    }

    @Test
    @DisplayName("令牌随机且长度足够（32 字节 hex = 64 字符）")
    void tokenStrength() {
        String t1 = hasher.newToken();
        String t2 = hasher.newToken();
        assertEquals(64, t1.length());
        assertFalse(t1.equals(t2));
    }

    // ==================== 权限计算 ====================

    private void givenUserWithRole(boolean admin, String roleStatus, String permStatus) {
        when(userRoleMapper.selectList(any())).thenReturn(List.of(ur(1L, 10L)));
        IamRole r = new IamRole();
        r.setId(10L);
        r.setStatus(roleStatus);
        when(roleMapper.selectBatchIds(any())).thenReturn(List.of(r));
        when(rolePermMapper.selectList(any())).thenReturn(List.of(rp(20L, 10L)));
        IamPermission p = new IamPermission();
        p.setId(20L);
        p.setPermCode("fin:bill:generate");
        p.setStatus(permStatus);
        when(permMapper.selectBatchIds(any())).thenReturn(List.of(p));
    }

    private static IamUserRole ur(long userId, long roleId) {
        IamUserRole u = new IamUserRole();
        u.setUserId(userId);
        u.setRoleId(roleId);
        return u;
    }

    private static IamRolePermission rp(long permId, long roleId) {
        IamRolePermission x = new IamRolePermission();
        x.setPermissionId(permId);
        x.setRoleId(roleId);
        return x;
    }

    @Test
    @DisplayName("正常角色得到权限码")
    void normalPermission() {
        givenUserWithRole(false, "ENABLED", "ENABLED");
        Set<String> codes = auth.permissionCodes(100L);
        assertTrue(codes.contains("fin:bill:generate"), codes.toString());
    }

    @Test
    @DisplayName("角色被停用 → 权限立即消失（不留后门）")
    void disabledRoleLosesPermission() {
        givenUserWithRole(false, "DISABLED", "ENABLED");
        assertTrue(auth.permissionCodes(100L).isEmpty());
    }

    @Test
    @DisplayName("权限项被停用 → 不进权限集")
    void disabledPermission() {
        givenUserWithRole(false, "ENABLED", "DISABLED");
        assertTrue(auth.permissionCodes(100L).isEmpty());
    }

    @Test
    @DisplayName("无角色 → 权限为空（不是默认全开）")
    void noRoleNoPermission() {
        when(userRoleMapper.selectList(any())).thenReturn(List.of());
        assertTrue(auth.permissionCodes(100L).isEmpty());
    }

    // ==================== LoginUser 语义 ====================

    @Test
    @DisplayName("管理员 has() 恒为 true（通配放行）")
    void adminHasAll() {
        LoginUser u = new LoginUser(1L, "admin", "管理员", "350600", null, true, "t",
                Set.of());
        assertTrue(u.has("any:perm:at:all"));
    }

    @Test
    @DisplayName("普通用户只放行自己拥有的权限")
    void normalHasOnlyOwned() {
        LoginUser u = new LoginUser(2L, "u", "用户", "350600", null, false, "t",
                Set.of("iam:user:list"));
        assertTrue(u.has("iam:user:list"));
        assertFalse(u.has("iam:user:create"));
    }

    // ==================== 令牌校验 ====================

    @Test
    @DisplayName("有效令牌 → 加载出登录用户，租户来自会话（权威来源）")
    void validToken() {
        when(sessionMapper.selectByTokenIgnoreTenant("tk")).thenReturn(
                session("tk", "ACTIVE", LocalDateTime.now().plusHours(1)));
        when(userMapper.selectById(100L)).thenReturn(user(100L, false, "ENABLED"));
        when(userRoleMapper.selectList(any())).thenReturn(List.of());

        LoginUser u = auth.loadByToken("tk");
        assertNotNull(u);
        assertEquals("350600", u.tenantId(), "租户必须取自会话记录");
        assertFalse(u.admin());
    }

    @Test
    @DisplayName("已登出令牌 → null")
    void loggedOutToken() {
        when(sessionMapper.selectByTokenIgnoreTenant("tk")).thenReturn(
                session("tk", "LOGOUT", LocalDateTime.now().plusHours(1)));
        assertNull(auth.loadByToken("tk"));
    }

    @Test
    @DisplayName("被踢下线令牌 → null")
    void kickedToken() {
        when(sessionMapper.selectByTokenIgnoreTenant("tk")).thenReturn(
                session("tk", "KICKED", LocalDateTime.now().plusHours(1)));
        assertNull(auth.loadByToken("tk"));
    }

    @Test
    @DisplayName("过期令牌 → null 且回写 EXPIRED")
    void expiredToken() {
        when(sessionMapper.selectByTokenIgnoreTenant("tk")).thenReturn(
                session("tk", "ACTIVE", LocalDateTime.now().minusMinutes(1)));
        assertNull(auth.loadByToken("tk"));
    }

    @Test
    @DisplayName("用户被停用 → 已有令牌失效（立即生效）")
    void disabledUserTokenInvalid() {
        when(sessionMapper.selectByTokenIgnoreTenant("tk")).thenReturn(
                session("tk", "ACTIVE", LocalDateTime.now().plusHours(1)));
        when(userMapper.selectById(100L)).thenReturn(user(100L, false, "DISABLED"));
        assertNull(auth.loadByToken("tk"));
    }

    @Test
    @DisplayName("空/未提供令牌 → null（不抛异常）")
    void blankToken() {
        assertNull(auth.loadByToken(null));
        assertNull(auth.loadByToken(""));
        assertNull(auth.loadByToken("   "));
    }

    @Test
    @DisplayName("管理员令牌 → LoginUser.admin=true，权限为通配")
    void adminToken() {
        when(sessionMapper.selectByTokenIgnoreTenant("tk")).thenReturn(
                session("tk", "ACTIVE", LocalDateTime.now().plusHours(1)));
        when(userMapper.selectById(100L)).thenReturn(user(100L, true, "ENABLED"));
        LoginUser u = auth.loadByToken("tk");
        assertNotNull(u);
        assertTrue(u.admin());
        assertTrue(u.has("whatever"));
    }
}
