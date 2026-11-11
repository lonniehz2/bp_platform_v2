package com.yundao.platform.service;

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
public class ReportService {

    private final JdbcTemplate jdbc;
    private final DataScopeService dataScope;

    public ReportService(JdbcTemplate jdbc, DataScopeService dataScope) {
        this.jdbc = jdbc;
        this.dataScope = dataScope;
    }

    public List<Map<String, Object>> projectCompare(String sceneCode) {
        String tenant = TenantContext.require();
        Set<Long> scope = dataScope.projectIds();
        List<Map<String, Object>> projects = jdbc.queryForList(
                "select id, org_code orgCode, org_name orgName from bp_org where tenant_id=? and scene_code=? and org_type='PROJECT' and status='ENABLED' and is_deleted=0 order by sort_no, id", tenant, sceneCode);
        List<Map<String, Object>> out = new ArrayList<>();
        for (Map<String, Object> p : projects) {
            long id = ((Number) p.get("id")).longValue();
            if (scope != null && !scope.contains(id)) continue;
            out.add(metrics(tenant, id, p));
        }
        return out;
    }

    public Map<String, Object> cockpit(long projectId, String sceneCode) {
        String tenant = TenantContext.require();
        Set<Long> scope = dataScope.projectIds();
        if (scope != null && !scope.contains(projectId)) throw new BizException("BP40300", "无权查看该项目经营数据", 403);
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select id, org_code orgCode, org_name orgName from bp_org where tenant_id=? and id=? and scene_code=? and is_deleted=0", tenant, projectId, sceneCode);
        if (rows.isEmpty()) throw BizException.notFound("项目不存在");
        return metrics(tenant, projectId, rows.get(0));
    }

    private Map<String, Object> metrics(String tenant, long projectId, Map<String, Object> project) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("projectId", projectId);
        m.put("orgCode", project.get("orgCode"));
        m.put("orgName", project.get("orgName"));
        Map<String, Object> houses = jdbc.queryForMap(
                "select count(*) total, sum(case when house_status in ('RENTED','OCCUPIED','ALLOCATED') then 1 else 0 end) rented, sum(case when house_status='VACANT' then 1 else 0 end) vacant from bp_house where tenant_id=? and org_id=? and is_deleted=0", tenant, projectId);
        long total = number(houses.get("total"));
        long rented = number(houses.get("rented"));
        m.put("houses", total);
        m.put("rentedHouses", rented);
        m.put("vacantHouses", number(houses.get("vacant")));
        m.put("occupancyRate", total == 0 ? 0 : Math.round(rented * 1000.0 / total) / 10.0);
        m.put("activeContracts", number(jdbc.queryForObject(
                "select count(*) from guarantee_contract where tenant_id=? and project_id=? and contract_status='ACTIVE' and is_deleted=0", Long.class, tenant, projectId)));
        Map<String, Object> bills = jdbc.queryForMap(
                "select coalesce(sum(payable_amount),0) receivable, coalesce(sum(paid_amount),0) received, coalesce(sum(greatest(payable_amount-paid_amount,0)),0) outstanding, count(*) billCount from bp_bill where tenant_id=? and project_id=? and is_deleted=0", tenant, projectId);
        double receivable = decimal(bills.get("receivable"));
        double received = decimal(bills.get("received"));
        m.put("receivable", receivable);
        m.put("received", received);
        m.put("outstanding", decimal(bills.get("outstanding")));
        m.put("collectionRate", receivable == 0 ? 0 : Math.round(received * 1000.0 / receivable) / 10.0);
        m.put("billCount", number(bills.get("billCount")));
        Map<String, Object> work = jdbc.queryForMap(
                "select count(*) total, sum(case when order_status in ('DONE','CLOSED') then 1 else 0 end) done from guarantee_work_order where tenant_id=? and project_id=? and is_deleted=0", tenant, projectId);
        long workTotal = number(work.get("total"));
        m.put("workOrders", workTotal);
        m.put("workOrderDone", number(work.get("done")));
        m.put("workOrderRate", workTotal == 0 ? 0 : Math.round(number(work.get("done")) * 1000.0 / workTotal) / 10.0);
        m.put("devices", number(jdbc.queryForObject("select count(*) from bp_dev_device where tenant_id=? and project_id=? and is_deleted=0", Long.class, tenant, projectId)));
        m.put("alerts", number(jdbc.queryForObject("select count(*) from guarantee_alert where tenant_id=? and project_id=? and alert_status='PENDING' and is_deleted=0", Long.class, tenant, projectId)));
        return m;
    }

    private static long number(Object v) { return v instanceof Number n ? n.longValue() : 0; }
    private static double decimal(Object v) { return v instanceof Number n ? n.doubleValue() : 0; }
}
