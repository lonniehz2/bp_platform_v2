package com.yundao.platform.service;

import com.yundao.platform.common.auth.UserContext;
import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.tenant.TenantContext;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class RelationService {

    private final JdbcTemplate jdbc;
    private final DataScopeService dataScope;

    public RelationService(JdbcTemplate jdbc, DataScopeService dataScope) {
        this.jdbc = jdbc;
        this.dataScope = dataScope;
    }

    public Map<String, Object> contract(long contractId) {
        String tenant = TenantContext.require();
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select c.id, c.contract_no contractNo, c.project_id projectId, c.person_id personId, c.house_id houseId, "
                        + "c.contract_status contractStatus, p.person_name personName, h.house_name houseName "
                        + "from guarantee_contract c left join bp_person p on p.id=c.person_id "
                        + "left join bp_house h on h.id=c.house_id "
                        + "where c.id=? and c.tenant_id=? and c.is_deleted=0", contractId, tenant);
        if (rows.isEmpty()) throw BizException.notFound("合同不存在");
        Map<String, Object> c = rows.get(0);
        long projectId = ((Number) c.get("projectId")).longValue();
        if (!canView("contracts", projectId)) throw new BizException("BP40300", "无权访问该合同", 403);

        List<Map<String, Object>> links = new ArrayList<>();
        links.add(personLink(c, projectId));
        links.add(houseLink(c, projectId));
        links.add(billLink(c, projectId));
        links.add(depositLink(c, projectId));

        Map<String, Object> out = new LinkedHashMap<>();
        out.put("entity", Map.of("type", "CONTRACT", "id", String.valueOf(contractId), "title", c.get("contractNo")));
        out.put("links", links);
        return out;
    }

    private Map<String, Object> personLink(Map<String, Object> c, long projectId) {
        boolean ok = canView("person", projectId);
        long id = c.get("personId") == null ? 0 : ((Number) c.get("personId")).longValue();
        String name = c.get("personName") == null ? "承租人" : String.valueOf(c.get("personName"));
        return link("PERSON", id == 0 ? null : String.valueOf(id), "承租人",
                ok ? name : mask(name), ok ? null : "无人员查看权限",
                "/guarantee/persons?id=" + id, ok);
    }

    private Map<String, Object> houseLink(Map<String, Object> c, long projectId) {
        boolean ok = canView("houses", projectId);
        long id = c.get("houseId") == null ? 0 : ((Number) c.get("houseId")).longValue();
        String name = c.get("houseName") == null ? "房屋" : String.valueOf(c.get("houseName"));
        return link("HOUSE", id == 0 ? null : String.valueOf(id), "房屋",
                ok ? name : "无权限查看房屋", ok ? null : "无房源查看权限",
                "/guarantee/houses?id=" + id, ok);
    }

    private Map<String, Object> billLink(Map<String, Object> c, long projectId) {
        boolean ok = canView("billing", projectId);
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select count(*) cnt, coalesce(sum(payable_amount),0) payable, coalesce(sum(paid_amount),0) paid "
                        + "from bp_bill where tenant_id=? and contract_id=? and is_deleted=0",
                TenantContext.require(), c.get("id"));
        Map<String, Object> row = rows.get(0);
        long count = ((Number) row.get("cnt")).longValue();
        double unpaid = ((Number) row.get("payable")).doubleValue() - ((Number) row.get("paid")).doubleValue();
        return link("BILLS", null, "账单",
                ok ? count + " 笔 · 未收 " + String.format("%.2f", Math.max(0, unpaid)) : "无账单查看权限",
                ok ? null : "无账单查看权限", "/guarantee/billing?contractId=" + c.get("id"), ok);
    }

    private Map<String, Object> depositLink(Map<String, Object> c, long projectId) {
        boolean ok = canView("deposits", projectId);
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select count(*) cnt, coalesce(sum(amount),0) amount from guarantee_deposit where tenant_id=? and contract_id=? and is_deleted=0",
                TenantContext.require(), c.get("id"));
        Map<String, Object> row = rows.get(0);
        long count = ((Number) row.get("cnt")).longValue();
        return link("DEPOSIT", null, "押金",
                ok ? count + " 笔 · " + String.format("%.2f", ((Number) row.get("amount")).doubleValue()) : "无押金查看权限",
                ok ? null : "无押金查看权限", "/guarantee/deposits?contractId=" + c.get("id"), ok);
    }

    private Map<String, Object> link(String type, String id, String label, String title, String reason,
                                     String route, boolean accessible) {
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("type", type);
        out.put("id", id);
        out.put("label", label);
        out.put("title", title);
        out.put("accessible", accessible);
        out.put("reason", reason);
        out.put("route", route);
        return out;
    }

    private boolean canView(String menuCode, long projectId) {
        UserContext.Principal p = UserContext.require();
        String tenant = p.tenantId();
        List<String> roles = jdbc.queryForList(
                "select r.role_code from bp_user_role ur join bp_role r on r.id=ur.role_id "
                        + "where ur.tenant_id=? and ur.user_id=? and r.role_status='ENABLED'",
                String.class, tenant, p.userId());
        if (roles.contains("GUARANTEE_ADMIN") || roles.contains("ADMIN")) return true;
        Long page = jdbc.queryForObject(
                "select count(*) from bp_user_role ur join bp_role_menu rm on rm.role_id=ur.role_id "
                        + "join bp_menu m on m.id=rm.menu_id where ur.tenant_id=? and ur.user_id=? "
                        + "and m.menu_code=? and m.scene_code='GUARANTEE' and m.menu_status='ENABLED'",
                Long.class, tenant, p.userId(), menuCode);
        if (page == null || page == 0) return false;
        Long configured = jdbc.queryForObject(
                "select count(*) from bp_user_role ur join bp_role_action ra on ra.role_id=ur.role_id "
                        + "where ur.tenant_id=? and ur.user_id=? and ra.menu_code=?",
                Long.class, tenant, p.userId(), menuCode);
        if (configured != null && configured > 0) {
            Long view = jdbc.queryForObject(
                    "select count(*) from bp_user_role ur join bp_role_action ra on ra.role_id=ur.role_id "
                            + "where ur.tenant_id=? and ur.user_id=? and ra.menu_code=? and ra.action_code in ('view','*')",
                    Long.class, tenant, p.userId(), menuCode);
            if (view == null || view == 0) return false;
        }
        Set<Long> scope = dataScope.projectIds();
        return scope == null || scope.contains(projectId);
    }

    private String mask(String name) {
        if (name == null || name.isBlank()) return "—";
        if (name.length() == 1) return name + "*";
        return name.substring(0, 1) + "*".repeat(Math.min(3, name.length() - 1));
    }
}
