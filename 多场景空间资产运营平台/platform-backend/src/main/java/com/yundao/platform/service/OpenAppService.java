package com.yundao.platform.service;

import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.id.IdGenerator;
import com.yundao.platform.common.tenant.TenantContext;
import java.security.SecureRandom;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class OpenAppService {

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;
    private final SecureRandom random = new SecureRandom();

    public OpenAppService(JdbcTemplate jdbc, IdGenerator idGen) {
        this.jdbc = jdbc;
        this.idGen = idGen;
    }

    public List<Map<String, Object>> list() {
        return jdbc.queryForList(
                "select id, app_code appCode, app_name appName, scopes, app_status appStatus, create_time createTime "
                        + "from guarantee_open_app where tenant_id=? and is_deleted=0 order by id desc",
                TenantContext.require());
    }

    public Map<String, Object> create(CreateCmd cmd) {
        if (cmd.appCode() == null || cmd.appCode().isBlank()
                || cmd.appName() == null || cmd.appName().isBlank()) {
            throw BizException.param("应用编码和名称不能为空");
        }
        String secret = newSecret();
        long id = idGen.nextId();
        try {
            jdbc.update("insert into guarantee_open_app(id,tenant_id,app_code,app_name,app_secret,scopes,"
                            + "app_status,is_deleted) values(?,?,?,?,?,?, 'ENABLED',0)",
                    id, TenantContext.require(), cmd.appCode().trim(), cmd.appName().trim(),
                    secret, cmd.scopes());
        } catch (DataIntegrityViolationException e) {
            throw BizException.conflict("应用编码已存在");
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", id);
        out.put("appCode", cmd.appCode());
        out.put("appSecret", secret);
        out.put("appStatus", "ENABLED");
        return out;
    }

    public Map<String, Object> toggle(long id, boolean enabled) {
        long updated = jdbc.update("update guarantee_open_app set app_status=?, update_time=now() "
                        + "where id=? and tenant_id=? and is_deleted=0",
                enabled ? "ENABLED" : "DISABLED", id, TenantContext.require());
        if (updated == 0) {
            throw BizException.notFound("应用不存在");
        }
        return Map.of("id", id, "appStatus", enabled ? "ENABLED" : "DISABLED");
    }

    private String newSecret() {
        byte[] bytes = new byte[32];
        random.nextBytes(bytes);
        return Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
    }

    public record CreateCmd(String appCode, String appName, String scopes) {
    }
}
