package com.yundao.platform.service;

import com.yundao.platform.common.auth.UserContext;
import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.id.IdGenerator;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class UserService {

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;
    private final BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();

    public UserService(JdbcTemplate jdbc, IdGenerator idGen) {
        this.jdbc = jdbc;
        this.idGen = idGen;
    }

    public List<Map<String, Object>> users() {
        String tenant = UserContext.require().tenantId();
        List<Map<String, Object>> users = jdbc.queryForList(
                "select id, username, display_name displayName, user_status userStatus, create_time createTime "
                        + "from bp_user where tenant_id=? and is_deleted=0 order by id",
                tenant);
        List<Map<String, Object>> links = jdbc.queryForList(
                "select ur.user_id userId, r.role_code roleCode, r.role_name roleName "
                        + "from bp_user_role ur join bp_role r on r.id=ur.role_id "
                        + "where ur.tenant_id=? order by r.role_name", tenant);
        for (Map<String, Object> user : users) {
            List<String> codes = new ArrayList<>();
            List<String> names = new ArrayList<>();
            for (Map<String, Object> link : links) {
                if (String.valueOf(link.get("userId")).equals(String.valueOf(user.get("id")))) {
                    codes.add(String.valueOf(link.get("roleCode")));
                    names.add(String.valueOf(link.get("roleName")));
                }
            }
            user.put("roleCodes", codes);
            user.put("roleNames", names);
        }
        return users;
    }

    public List<Map<String, Object>> roles() {
        return jdbc.queryForList(
                "select id, role_code roleCode, role_name roleName from bp_role "
                        + "where tenant_id=? and scene_code='GUARANTEE' and is_deleted=0 order by id",
                UserContext.require().tenantId());
    }

    @Transactional
    public Map<String, Object> create(CreateCmd cmd) {
        String tenant = UserContext.require().tenantId();
        if (cmd.username() == null || cmd.username().isBlank()
                || cmd.password() == null || cmd.password().length() < 6
                || cmd.displayName() == null || cmd.displayName().isBlank()) {
            throw BizException.param("用户名、姓名必填，密码至少 6 位");
        }
        Long exists = jdbc.queryForObject(
                "select count(*) from bp_user where tenant_id=? and username=? and is_deleted=0",
                Long.class, tenant, cmd.username().trim());
        if (exists != null && exists > 0) {
            throw BizException.conflict("用户名已存在");
        }
        long userId = idGen.nextId();
        try {
            jdbc.update("insert into bp_user(id,tenant_id,username,password_hash,display_name,user_status,is_deleted) "
                            + "values(?,?,?,?,?, 'ENABLED',0)",
                    userId, tenant, cmd.username().trim(), encoder.encode(cmd.password()),
                    cmd.displayName().trim());
        } catch (DataIntegrityViolationException e) {
            throw BizException.conflict("用户名已存在");
        }
        bindRoles(userId, tenant, cmd.roleIds());
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", userId);
        out.put("username", cmd.username().trim());
        out.put("userStatus", "ENABLED");
        return out;
    }

    @Transactional
    public Map<String, Object> update(long userId, UpdateCmd cmd) {
        String tenant = UserContext.require().tenantId();
        if (cmd.userStatus() != null && !List.of("ENABLED", "DISABLED").contains(cmd.userStatus())) {
            throw BizException.param("用户状态不合法");
        }
        if (cmd.password() != null && !cmd.password().isBlank() && cmd.password().length() < 6) {
            throw BizException.param("密码至少 6 位");
        }
        int updated = jdbc.update("update bp_user set user_status=coalesce(?,user_status), "
                        + "display_name=coalesce(?,display_name), "
                        + "password_hash=case when ? is null or ?='' then password_hash else ? end, update_time=now() "
                        + "where id=? and tenant_id=? and is_deleted=0",
                cmd.userStatus(), cmd.displayName(), cmd.password(), cmd.password(),
                cmd.password() == null || cmd.password().isBlank() ? null : encoder.encode(cmd.password()),
                userId, tenant);
        if (updated == 0) {
            throw BizException.notFound("用户不存在");
        }
        if (cmd.roleIds() != null) {
            jdbc.update("delete from bp_user_role where tenant_id=? and user_id=?", tenant, userId);
            bindRoles(userId, tenant, cmd.roleIds());
        }
        return Map.of("id", userId, "userStatus",
                cmd.userStatus() == null ? "UNCHANGED" : cmd.userStatus());
    }

    private void bindRoles(long userId, String tenant, List<Long> roleIds) {
        if (roleIds == null || roleIds.isEmpty()) {
            return;
        }
        for (Long roleId : roleIds) {
            Long count = jdbc.queryForObject(
                    "select count(*) from bp_role where id=? and tenant_id=? and scene_code='GUARANTEE' and is_deleted=0",
                    Long.class, roleId, tenant);
            if (count == null || count == 0) {
                throw BizException.param("角色不合法");
            }
            jdbc.update("insert into bp_user_role(id,tenant_id,user_id,role_id) values(?,?,?,?)",
                    idGen.nextId(), tenant, userId, roleId);
        }
    }

    public record CreateCmd(String username, String password, String displayName, List<Long> roleIds) {
    }

    public record UpdateCmd(String userStatus, String displayName, String password, List<Long> roleIds) {
    }
}
