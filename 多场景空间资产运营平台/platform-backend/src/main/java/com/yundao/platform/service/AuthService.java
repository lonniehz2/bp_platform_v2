package com.yundao.platform.service;

import com.yundao.platform.common.auth.LegacyPasswordHasher;
import com.yundao.platform.common.auth.TokenService;
import com.yundao.platform.common.auth.UserContext;
import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.tenant.TenantContext;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;

@Service
public class AuthService {

    private final JdbcTemplate jdbc;
    private final TokenService tokenService;
    private final BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();

    public AuthService(JdbcTemplate jdbc, TokenService tokenService) {
        this.jdbc = jdbc;
        this.tokenService = tokenService;
    }

    public LoginResult login(LoginCmd cmd) {
        String tenant = cmd.tenantId() == null || cmd.tenantId().isBlank() ? "350600" : cmd.tenantId();
        if (cmd.username() == null || cmd.password() == null) {
            throw BizException.param("用户名和密码不能为空");
        }
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select id, username, password_hash passwordHash, display_name displayName, user_status status "
                        + "from bp_user where tenant_id=? and username=? and is_deleted=0",
                tenant, cmd.username());
        if (rows.isEmpty()) {
            throw new BizException("BP40101", "用户名或密码错误", 401);
        }
        Map<String, Object> user = rows.get(0);
        String passwordHash = String.valueOf(user.get("passwordHash"));
        boolean matched = passwordHash.startsWith("pbkdf2$")
                ? LegacyPasswordHasher.verify(cmd.password(), passwordHash)
                : encoder.matches(cmd.password(), passwordHash);
        if (!"ENABLED".equals(String.valueOf(user.get("status"))) || !matched) {
            throw new BizException("BP40101", "用户名或密码错误", 401);
        }
        long userId = ((Number) user.get("id")).longValue();
        if (passwordHash.startsWith("pbkdf2$")) {
            jdbc.update("update bp_user set password_hash=? where id=?", encoder.encode(cmd.password()), userId);
        }
        String displayName = String.valueOf(user.get("displayName"));
        String token = tokenService.create(userId, tenant, cmd.username(), displayName);
        return new LoginResult(token, userId, tenant, cmd.username(), displayName, roles(userId, tenant));
    }

    public UserContext.Principal me() {
        return UserContext.require();
    }

    public List<String> roles(long userId, String tenant) {
        return jdbc.queryForList(
                "select r.role_code roleCode from bp_user_role ur join bp_role r on r.id=ur.role_id "
                        + "where ur.tenant_id=? and ur.user_id=? and r.role_status='ENABLED' order by r.id",
                String.class, tenant, userId);
    }

    public List<String> menuCodes(long userId, String tenant, String sceneCode) {
        return jdbc.queryForList(
                "select distinct m.menu_code menuCode from bp_user_role ur "
                        + "join bp_role_menu rm on rm.role_id=ur.role_id "
                        + "join bp_menu m on m.id=rm.menu_id "
                        + "where ur.tenant_id=? and ur.user_id=? and m.scene_code=? "
                        + "and m.menu_status='ENABLED' order by m.menu_code",
                String.class, tenant, userId, sceneCode);
    }

    public String encode(String raw) {
        return encoder.encode(raw);
    }

    public record LoginCmd(String username, String password, String tenantId) {
    }

    public record LoginResult(String token, long userId, String tenantId, String username,
                              String displayName, List<String> roles) {
    }
}
