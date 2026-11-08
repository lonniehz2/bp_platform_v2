package com.yundao.platform.service;

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

    public MenuService(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
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
}
