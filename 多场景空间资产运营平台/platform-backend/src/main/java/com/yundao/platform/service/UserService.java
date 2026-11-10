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
                "select u.id, u.username, u.display_name displayName, u.user_status userStatus, u.create_time createTime, "
                        + "(select count(*) from bp_user_scope_override o where o.tenant_id=u.tenant_id and o.user_id=u.id and o.enabled=1) scopeOverrideEnabled, "
                        + "(select count(*) from bp_user_project p where p.tenant_id=u.tenant_id and p.user_id=u.id and p.is_deleted=0) scopeProjectCount, "
                        + "(select count(*) from bp_user_org g where g.tenant_id=u.tenant_id and g.user_id=u.id and g.is_deleted=0) scopeOrgCount "
                        + "from bp_user u where u.tenant_id=? and u.is_deleted=0 order by u.id",
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


    public Map<String, Object> scopes(long userId) {
        String tenant = UserContext.require().tenantId();
        Long exists = jdbc.queryForObject(
                "select count(*) from bp_user where id=? and tenant_id=? and is_deleted=0",
                Long.class, userId, tenant);
        if (exists == null || exists == 0) {
            throw BizException.notFound("用户不存在");
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("userId", userId);
        out.put("projectIds", jdbc.queryForList(
                "select project_id from bp_user_project where tenant_id=? and user_id=? and is_deleted=0",
                Long.class, tenant, userId));
        out.put("orgIds", jdbc.queryForList(
                "select org_id from bp_user_org where tenant_id=? and user_id=? and is_deleted=0",
                Long.class, tenant, userId));
        List<Integer> overrides = jdbc.queryForList(
                "select enabled from bp_user_scope_override where tenant_id=? and user_id=?",
                Integer.class, tenant, userId);
        out.put("overrideEnabled", !overrides.isEmpty() && overrides.get(0) != null && overrides.get(0) == 1);
        return out;
    }

    @Transactional
    public Map<String, Object> updateScopes(long userId, ScopeCmd cmd) {
        String tenant = UserContext.require().tenantId();
        Long exists = jdbc.queryForObject(
                "select count(*) from bp_user where id=? and tenant_id=? and is_deleted=0",
                Long.class, userId, tenant);
        if (exists == null || exists == 0) {
            throw BizException.notFound("用户不存在");
        }
        jdbc.update("delete from bp_user_project where tenant_id=? and user_id=?", tenant, userId);
        jdbc.update("delete from bp_user_org where tenant_id=? and user_id=?", tenant, userId);
        boolean override = Boolean.TRUE.equals(cmd.overrideEnabled());
        if (override && cmd.projectIds() != null) {
            for (Long projectId : cmd.projectIds()) {
                Long count = jdbc.queryForObject(
                        "select count(*) from bp_org where id=? and tenant_id=? and is_deleted=0",
                        Long.class, projectId, tenant);
                if (count == null || count == 0) throw BizException.param("项目不合法");
                jdbc.update("insert into bp_user_project(id,tenant_id,user_id,project_id,is_default,is_deleted) "
                                + "values(?,?,?,?,0,0)",
                        idGen.nextId(), tenant, userId, projectId);
            }
        }
        if (override && cmd.orgIds() != null) {
            for (Long orgId : cmd.orgIds()) {
                Long count = jdbc.queryForObject(
                        "select count(*) from bp_org where id=? and tenant_id=? and is_deleted=0",
                        Long.class, orgId, tenant);
                if (count == null || count == 0) throw BizException.param("组织不合法");
                jdbc.update("insert into bp_user_org(id,tenant_id,user_id,org_id,is_deleted) values(?,?,?,?,0)",
                        idGen.nextId(), tenant, userId, orgId);
            }
        }
        jdbc.update("insert into bp_user_scope_override(user_id,tenant_id,enabled) values(?,?,?) "
                        + "on duplicate key update enabled=values(enabled)",
                userId, tenant, override ? 1 : 0);
        return scopes(userId);
    }


    @Transactional
    public Map<String, Object> archive(long userId) {
        UserContext.Principal principal = UserContext.require();
        if (principal.userId() == userId) throw BizException.conflict("不能删除当前登录用户");
        String tenant = principal.tenantId();
        Long exists = jdbc.queryForObject(
                "select count(*) from bp_user where id=? and tenant_id=? and is_deleted=0",
                Long.class, userId, tenant);
        if (exists == null || exists == 0) throw BizException.notFound("用户不存在");
        List<String> roles = jdbc.queryForList(
                "select r.role_code from bp_user_role ur join bp_role r on r.id=ur.role_id where ur.tenant_id=? and ur.user_id=?",
                String.class, tenant, userId);
        if (roles.contains("GUARANTEE_ADMIN") || roles.contains("ADMIN")) {
            Long admins = jdbc.queryForObject(
                    "select count(distinct u.id) from bp_user u join bp_user_role ur on ur.user_id=u.id "
                            + "join bp_role r on r.id=ur.role_id where u.tenant_id=? and u.is_deleted=0 "
                            + "and r.role_code in ('GUARANTEE_ADMIN','ADMIN')", Long.class, tenant);
            if (admins == null || admins <= 1) throw BizException.conflict("不能删除最后一个管理员");
        }
        jdbc.update("update bp_user set is_deleted=1, user_status='DISABLED' where id=? and tenant_id=?", userId, tenant);
        jdbc.update("delete from bp_user_role where tenant_id=? and user_id=?", tenant, userId);
        jdbc.update("delete from bp_user_project where tenant_id=? and user_id=?", tenant, userId);
        jdbc.update("delete from bp_user_org where tenant_id=? and user_id=?", tenant, userId);
        jdbc.update("delete from bp_user_scope_override where tenant_id=? and user_id=?", tenant, userId);
        return Map.of("id", userId, "status", "ARCHIVED");
    }


    public Map<String, Object> effectivePermissions(long userId) {
        String tenant = UserContext.require().tenantId();
        List<String> roles = jdbc.queryForList(
                "select r.role_code from bp_user_role ur join bp_role r on r.id=ur.role_id "
                        + "where ur.tenant_id=? and ur.user_id=? and r.role_status='ENABLED'", String.class, tenant, userId);
        List<String> pages = jdbc.queryForList(
                "select distinct m.menu_code from bp_user_role ur join bp_role_menu rm on rm.role_id=ur.role_id "
                        + "join bp_menu m on m.id=rm.menu_id where ur.tenant_id=? and ur.user_id=? and m.menu_type='PAGE' "
                        + "and m.menu_status='ENABLED' order by m.menu_code", String.class, tenant, userId);
        List<String> actions = jdbc.queryForList(
                "select distinct concat(ra.menu_code,':',ra.action_code) from bp_user_role ur "
                        + "join bp_role_action ra on ra.role_id=ur.role_id where ur.tenant_id=? and ur.user_id=? "
                        + "order by 1", String.class, tenant, userId);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("roles", roles); out.put("pageCodes", pages); out.put("actionCodes", actions);
        return out;
    }

    public Map<String, Object> effectiveScope(long userId) {
        String tenant = UserContext.require().tenantId();
        List<String> roles = jdbc.queryForList(
                "select r.role_code from bp_user_role ur join bp_role r on r.id=ur.role_id "
                        + "where ur.tenant_id=? and ur.user_id=? and r.role_status='ENABLED'", String.class, tenant, userId);
        List<Map<String, Object>> scopes = jdbc.queryForList(
                "select r.role_code roleCode, rs.scope_type scopeType from bp_user_role ur "
                        + "join bp_role r on r.id=ur.role_id left join bp_role_scope rs on rs.role_id=r.id "
                        + "where ur.tenant_id=? and ur.user_id=?", tenant, userId);
        List<Long> roleProjects = jdbc.queryForList(
                "select distinct rp.project_id from bp_user_role ur join bp_role_project rp on rp.role_id=ur.role_id "
                        + "where ur.tenant_id=? and ur.user_id=?", Long.class, tenant, userId);
        List<Integer> override = jdbc.queryForList(
                "select enabled from bp_user_scope_override where tenant_id=? and user_id=?", Integer.class, tenant, userId);
        boolean overrideEnabled = !override.isEmpty() && override.get(0) != null && override.get(0) == 1;
        List<Long> userProjects = jdbc.queryForList(
                "select project_id from bp_user_project where tenant_id=? and user_id=? and is_deleted=0",
                Long.class, tenant, userId);
        boolean all = scopes.stream().anyMatch(x -> "ALL".equals(x.get("scopeType")));
        List<Long> effective = new java.util.ArrayList<>();
        if (all && !overrideEnabled) {
            effective = null;
        } else if (overrideEnabled) {
            effective.addAll(userProjects);
        } else if (!roleProjects.isEmpty()) {
            effective.addAll(roleProjects);
        } else {
            effective.addAll(userProjects);
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("roles", roles); out.put("roleScopes", scopes);
        out.put("overrideEnabled", overrideEnabled);
        out.put("userProjectIds", userProjects);
        out.put("effectiveProjectIds", effective);
        out.put("allProjects", effective == null);
        return out;
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

    public record ScopeCmd(List<Long> projectIds, List<Long> orgIds, Boolean overrideEnabled) {
    }
}
