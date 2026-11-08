package com.yundao.platform.service;

import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.id.IdGenerator;
import com.yundao.platform.common.tenant.TenantContext;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class MenuService {

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;

    public MenuService(JdbcTemplate jdbc, IdGenerator idGen) {
        this.jdbc = jdbc;
        this.idGen = idGen;
    }

    public List<Map<String, Object>> menuTree(String sceneCode) {
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select menu_code menuCode, parent_code parentCode, menu_name menuName, menu_type menuType, "
                        + "route, sort_no sortNo from bp_menu where scene_code=? and menu_status='ENABLED' "
                        + "order by sort_no, menu_code", sceneCode);
        Map<String, Map<String, Object>> byCode = new LinkedHashMap<>();
        for (Map<String, Object> row : rows) {
            Map<String, Object> node = new LinkedHashMap<>();
            node.put("menuCode", row.get("menuCode"));
            node.put("menuName", row.get("menuName"));
            node.put("menuType", row.get("menuType"));
            node.put("route", row.get("route"));
            node.put("sortNo", row.get("sortNo"));
            node.put("children", new ArrayList<Map<String, Object>>());
            byCode.put(String.valueOf(row.get("menuCode")), node);
        }
        List<Map<String, Object>> roots = new ArrayList<>();
        for (Map<String, Object> row : rows) {
            Map<String, Object> node = byCode.get(String.valueOf(row.get("menuCode")));
            String parent = row.get("parentCode") == null ? null : String.valueOf(row.get("parentCode"));
            if (parent == null || !byCode.containsKey(parent)) {
                roots.add(node);
            } else {
                @SuppressWarnings("unchecked")
                List<Map<String, Object>> children = (List<Map<String, Object>>) byCode.get(parent).get("children");
                children.add(node);
            }
        }
        return roots;
    }

    public List<Map<String, Object>> roles(String sceneCode) {
        return jdbc.queryForList(
                "select r.id, r.scene_code sceneCode, r.role_code roleCode, r.role_name roleName, "
                        + "r.role_status roleStatus, count(rm.id) menuCount "
                        + "from bp_role r left join bp_role_menu rm on rm.role_id=r.id "
                        + "where r.tenant_id=? and r.scene_code=? and r.is_deleted=0 "
                        + "group by r.id, r.scene_code, r.role_code, r.role_name, r.role_status "
                        + "order by r.id", TenantContext.require(), sceneCode);
    }

    public List<Map<String, Object>> roleMenus(long roleId) {
        return jdbc.queryForList(
                "select m.menu_code menuCode, m.parent_code parentCode, m.menu_name menuName, "
                        + "m.route, m.sort_no sortNo from bp_role_menu rm join bp_menu m on m.id=rm.menu_id "
                        + "where rm.tenant_id=? and rm.role_id=? order by m.sort_no, m.menu_code",
                TenantContext.require(), roleId);
    }

    public Map<String, Object> createRole(CreateRoleCmd cmd) {
        String tenant = TenantContext.require();
        if (cmd.sceneCode() == null || cmd.sceneCode().isBlank()
                || cmd.roleCode() == null || cmd.roleCode().isBlank()
                || cmd.roleName() == null || cmd.roleName().isBlank()) {
            throw BizException.param("场景、角色编码、角色名称不能为空");
        }
        Long exists = jdbc.queryForObject(
                "select count(*) from bp_role where tenant_id=? and scene_code=? and role_code=? and is_deleted=0",
                Long.class, tenant, cmd.sceneCode(), cmd.roleCode().trim());
        if (exists != null && exists > 0) {
            throw BizException.conflict("角色编码已存在");
        }
        long id = idGen.nextId();
        jdbc.update("insert into bp_role(id,tenant_id,scene_code,role_code,role_name,role_status,is_deleted) "
                        + "values(?,?,?,?,?, 'ENABLED',0)",
                id, tenant, cmd.sceneCode(), cmd.roleCode().trim(), cmd.roleName().trim());
        if (cmd.menuCodes() != null) {
            insertMenus(id, cmd.menuCodes());
        }
        return Map.of("id", id, "roleCode", cmd.roleCode(), "roleName", cmd.roleName());
    }

    public Map<String, Object> saveMenus(long roleId, List<String> menuCodes) {
        String tenant = TenantContext.require();
        Long count = jdbc.queryForObject(
                "select count(*) from bp_role where id=? and tenant_id=? and is_deleted=0",
                Long.class, roleId, tenant);
        if (count == null || count == 0) {
            throw BizException.notFound("角色不存在");
        }
        jdbc.update("delete from bp_role_menu where tenant_id=? and role_id=?", tenant, roleId);
        insertMenus(roleId, menuCodes);
        return Map.of("roleId", roleId, "menuCount", menuCodes == null ? 0 : menuCodes.size());
    }

    private void insertMenus(long roleId, List<String> menuCodes) {
        String tenant = TenantContext.require();
        if (menuCodes == null) return;
        for (String code : menuCodes) {
            if (code == null || code.isBlank()) continue;
            Long menuId = jdbc.query("select id from bp_menu where menu_code=? and menu_status='ENABLED' limit 1",
                    rs -> rs.next() ? rs.getLong(1) : null, code);
            if (menuId != null) {
                jdbc.update("insert ignore into bp_role_menu(id,tenant_id,role_id,menu_id) values(?,?,?,?)",
                        idGen.nextId(), tenant, roleId, menuId);
            }
        }
    }

    public record CreateRoleCmd(String sceneCode, String roleCode, String roleName, List<String> menuCodes) {
    }
}
