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


    public Map<String, Object> person(long personId) {
        String tenant = TenantContext.require();
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select id, person_name personName, person_code personCode, org_id orgId from bp_person "
                        + "where id=? and tenant_id=? and is_deleted=0", personId, tenant);
        if (rows.isEmpty()) throw BizException.notFound("人员不存在");
        Map<String, Object> person = rows.get(0);
        Long orgId = person.get("orgId") == null ? null : ((Number) person.get("orgId")).longValue();
        boolean personOk = canViewPage("person") && (orgId == null || inScope(orgId));
        if (!personOk) throw new BizException("BP40300", "无权查看该人员", 403);

        List<Map<String, Object>> tenantContracts = new ArrayList<>();
        List<Map<String, Object>> cohabitantContracts = new ArrayList<>();
        List<Map<String, Object>> all = jdbc.queryForList(
                "select c.id, c.contract_no contractNo, c.project_id projectId, c.house_id houseId, h.house_name houseName, "
                        + "c.start_date startDate, c.end_date endDate, c.contract_status contractStatus, "
                        + "'TENANT' relationType, null mainTenantName from guarantee_contract c "
                        + "left join bp_house h on h.id=c.house_id where c.person_id=? and c.tenant_id=? and c.is_deleted=0 "
                        + "union all "
                        + "select c.id, c.contract_no contractNo, c.project_id projectId, c.house_id houseId, h.house_name houseName, "
                        + "c.start_date startDate, c.end_date endDate, c.contract_status contractStatus, "
                        + "'COHABITANT' relationType, p.person_name mainTenantName "
                        + "from guarantee_contract_cohabitant cc join guarantee_contract c on c.id=cc.contract_id "
                        + "left join bp_house h on h.id=c.house_id left join bp_person p on p.id=c.person_id "
                        + "where cc.person_id=? and cc.tenant_id=? and cc.is_deleted=0 and c.is_deleted=0",
                personId, tenant, personId, tenant);
        for (Map<String, Object> c : all) {
            long projectId = ((Number) c.get("projectId")).longValue();
            boolean ok = canView("contracts", projectId);
            Map<String, Object> item = new LinkedHashMap<>(c);
            item.put("accessible", ok);
            item.put("reason", ok ? null : "无合同查看权限");
            item.put("route", "/guarantee/contracts/" + c.get("id"));
            if (!ok) {
                item.put("contractNo", "无权限查看");
                item.put("houseName", null);
                item.put("startDate", null); item.put("endDate", null);
            }
            if ("TENANT".equals(c.get("relationType"))) tenantContracts.add(item);
            else cohabitantContracts.add(item);
        }

        List<Map<String, Object>> cohabitants = jdbc.queryForList(
                "select cc.contract_id contractId, cc.person_id personId, p.person_name personName, cc.relation_type relationType, "
                        + "cc.start_date startDate, cc.end_date endDate, cc.cohabitant_status status "
                        + "from guarantee_contract_cohabitant cc join bp_person p on p.id=cc.person_id "
                        + "where cc.tenant_id=? and cc.is_deleted=0 and cc.contract_id in "
                        + "(select id from guarantee_contract where tenant_id=? and person_id=? and is_deleted=0)",
                tenant, tenant, personId);
        List<Map<String, Object>> links = new ArrayList<>();
        long personProject = orgId == null ? 0 : orgId;
        long contractCount = tenantContracts.size() + cohabitantContracts.size();
        boolean contractOk = canView("contracts", personProject) && personProject > 0;
        links.add(link("CONTRACTS", null, "合同", contractOk ? contractCount + " 份" : "无合同查看权限",
                contractOk ? null : "无合同查看权限", "/guarantee/contracts", contractOk));
        long billCount = count("select count(*) from bp_bill where tenant_id=? and person_id=? and is_deleted=0", tenant, personId);
        boolean billOk = canView("billing", personProject) && personProject > 0;
        links.add(link("BILLS", null, "账单", billOk ? billCount + " 笔" : "无账单查看权限",
                billOk ? null : "无账单查看权限", "/guarantee/billing", billOk));
        long workOrderCount = count("select count(*) from guarantee_work_order where tenant_id=? and person_id=? and is_deleted=0", tenant, personId);
        boolean workOk = canView("workOrders", personProject) && personProject > 0;
        links.add(link("WORK_ORDERS", null, "工单", workOk ? workOrderCount + " 个" : "无工单查看权限",
                workOk ? null : "无工单查看权限", "/guarantee/work-orders", workOk));
        long accessCount = count("select count(*) from guarantee_access_record where tenant_id=? and person_id=? and is_deleted=0", tenant, personId);
        boolean accessOk = canView("accessRecords", personProject) && personProject > 0;
        links.add(link("ACCESS_RECORDS", null, "通行记录", accessOk ? accessCount + " 条" : "无通行查看权限",
                accessOk ? null : "无通行查看权限", "/guarantee/access", accessOk));

        Map<String, Object> out = new LinkedHashMap<>();
        out.put("person", person);
        out.put("tenantContracts", tenantContracts);
        out.put("cohabitantContracts", cohabitantContracts);
        out.put("cohabitants", cohabitants);
        out.put("links", links);
        return out;
    }

    private boolean canViewPage(String menuCode) {
        UserContext.Principal p = UserContext.require();
        Long page = jdbc.queryForObject(
                "select count(*) from bp_user_role ur join bp_role_menu rm on rm.role_id=ur.role_id "
                        + "join bp_menu m on m.id=rm.menu_id where ur.tenant_id=? and ur.user_id=? "
                        + "and m.menu_code=? and m.scene_code='GUARANTEE' and m.menu_status='ENABLED'",
                Long.class, p.tenantId(), p.userId(), menuCode);
        if (page == null || page == 0) return false;
        Long configured = jdbc.queryForObject(
                "select count(*) from bp_user_role ur join bp_role_action ra on ra.role_id=ur.role_id "
                        + "where ur.tenant_id=? and ur.user_id=? and ra.menu_code=?",
                Long.class, p.tenantId(), p.userId(), menuCode);
        if (configured != null && configured > 0) {
            Long view = jdbc.queryForObject(
                    "select count(*) from bp_user_role ur join bp_role_action ra on ra.role_id=ur.role_id "
                            + "where ur.tenant_id=? and ur.user_id=? and ra.menu_code=? and ra.action_code in ('view','*')",
                    Long.class, p.tenantId(), p.userId(), menuCode);
            return view != null && view > 0;
        }
        return true;
    }

    private boolean inScope(long projectId) {
        Set<Long> scope = dataScope.projectIds();
        return scope == null || scope.contains(projectId);
    }


    public Map<String, Object> sections(String type, long id) {
        String tenant = TenantContext.require();
        Map<String, Object> root;
        if ("CONTRACT".equalsIgnoreCase(type)) root = contract(id);
        else if ("PERSON".equalsIgnoreCase(type)) root = person(id);
        else if ("HOUSE".equalsIgnoreCase(type)) root = house(id);
        else if ("BILL".equalsIgnoreCase(type)) root = bill(id);
        else if ("DEVICE".equalsIgnoreCase(type)) root = device(id);
        else if ("WORK_ORDER".equalsIgnoreCase(type)) root = workOrder(id);
        else if ("APPLICATION".equalsIgnoreCase(type)) root = application(id);
        else throw new BizException("BP40004", "暂不支持该关联类型", 400);
        Map<String, Object> entity = entityOf(root, type, id);
        List<Map<String, Object>> sections = new ArrayList<>();
        sections.add(section("overview", "概览", true, null, List.of(entity)));
        String t = type.toUpperCase();
        if ("PERSON".equals(t)) sections.addAll(personSections(tenant, id, root));
        else if ("HOUSE".equals(t)) sections.addAll(houseSections(tenant, id));
        else if ("BILL".equals(t)) sections.addAll(billSections(tenant, id));
        else if ("DEVICE".equals(t)) sections.addAll(deviceSections(tenant, id));
        else if ("WORK_ORDER".equals(t)) sections.addAll(workOrderSections(tenant, id));
        else if ("APPLICATION".equals(t)) sections.addAll(applicationSections(tenant, id));
        else if ("CONTRACT".equals(t)) sections.addAll(contractSections(tenant, id));
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("entity", entity); out.put("sections", sections); return out;
    }

    private Map<String, Object> entityOf(Map<String, Object> root, String type, long id) {
        Map<String, Object> entity = new LinkedHashMap<>();
        if (root.get("entity") instanceof Map<?, ?> e) entity.putAll((Map<String, Object>) e);
        else if (root.get("person") instanceof Map<?, ?> p) {
            entity.put("type", "PERSON"); entity.put("id", String.valueOf(id));
            entity.put("title", p.get("personName")); entity.put("subtitle", p.get("personCode"));
            entity.put("phone", p.get("phone")); entity.put("personType", p.get("personType")); entity.put("status", p.get("status"));
        } else {
            entity.put("type", type.toUpperCase()); entity.put("id", String.valueOf(id));
            entity.put("title", root.getOrDefault("contractNo", "详情 #" + id));
            entity.put("subtitle", root.getOrDefault("contractStatus", null));
            for (String k : List.of("contractNo", "houseName", "startDate", "endDate", "rentAmount", "depositAmount", "contractStatus")) {
                if (root.get(k) != null) entity.put(k, root.get(k));
            }
            if (entity.get("contractStatus") != null) entity.put("status", entity.get("contractStatus"));
        }
        return entity;
    }

    private List<Map<String, Object>> columns(String key) {
        java.util.function.BiFunction<String, String, Map<String, Object>> c = (k, l) -> {
            Map<String, Object> m = new LinkedHashMap<>(); m.put("key", k); m.put("label", l); return m;
        };
        List<Map<String, Object>> list = new ArrayList<>();
        switch (key) {
            case "contracts" -> { list.add(c.apply("contractNo", "合同号")); list.add(c.apply("houseName", "房屋")); list.add(c.apply("startDate", "开始日期")); list.add(c.apply("endDate", "结束日期")); list.add(c.apply("status", "状态")); }
            case "bills" -> { list.add(c.apply("billNo", "账单号")); list.add(c.apply("periodStart", "账期起")); list.add(c.apply("periodEnd", "账期止")); list.add(c.apply("payableAmount", "应付")); list.add(c.apply("paidAmount", "已收")); list.add(c.apply("status", "状态")); }
            case "workOrders" -> { list.add(c.apply("orderNo", "工单号")); list.add(c.apply("title", "标题")); list.add(c.apply("assigneeName", "处理人")); list.add(c.apply("status", "状态")); }
            case "access" -> { list.add(c.apply("validStart", "通行时间")); list.add(c.apply("visitorName", "访客")); list.add(c.apply("purpose", "事由")); list.add(c.apply("status", "状态")); }
            case "devices" -> { list.add(c.apply("deviceCode", "设备编码")); list.add(c.apply("deviceName", "设备名称")); list.add(c.apply("deviceType", "类型")); list.add(c.apply("status", "状态")); }
            case "persons", "person" -> { list.add(c.apply("personName", "姓名")); list.add(c.apply("phone", "电话")); list.add(c.apply("personType", "人员类型")); list.add(c.apply("status", "状态")); }
            case "house" -> { list.add(c.apply("houseCode", "房源编码")); list.add(c.apply("houseName", "名称")); list.add(c.apply("houseStatus", "房态")); }
            case "contract" -> { list.add(c.apply("contractNo", "合同号")); list.add(c.apply("contractStatus", "合同状态")); }
            case "waitlist" -> { list.add(c.apply("queueNo", "轮候号")); list.add(c.apply("waitlistStatus", "状态")); }
            case "allocation" -> { list.add(c.apply("allocationNo", "配租单号")); list.add(c.apply("allocationStatus", "状态")); }
            case "payments" -> { list.add(c.apply("paymentNo", "收款单号")); list.add(c.apply("paymentMethod", "方式")); list.add(c.apply("amount", "金额")); list.add(c.apply("paidTime", "收款时间")); list.add(c.apply("status", "状态")); }
            case "grants" -> { list.add(c.apply("personName", "人员")); list.add(c.apply("grantLevel", "级别")); list.add(c.apply("validStart", "开始")); list.add(c.apply("validEnd", "结束")); list.add(c.apply("status", "状态")); }
            case "alerts" -> { list.add(c.apply("title", "告警")); list.add(c.apply("alertLevel", "级别")); list.add(c.apply("alertStatus", "状态")); }
            case "deposit" -> { list.add(c.apply("amount", "押金金额")); list.add(c.apply("refundedAmount", "已退")); list.add(c.apply("status", "状态")); }
            case "changes" -> { list.add(c.apply("changeType", "变更类型")); list.add(c.apply("effectiveDate", "生效日期")); list.add(c.apply("reason", "原因")); list.add(c.apply("status", "状态")); }
            case "files" -> { list.add(c.apply("fileName", "文件名")); list.add(c.apply("fileSize", "大小")); list.add(c.apply("createTime", "上传时间")); }
            case "subsidies" -> { list.add(c.apply("subsidyType", "补贴类型")); list.add(c.apply("amount", "金额")); list.add(c.apply("startDate", "开始")); list.add(c.apply("endDate", "结束")); list.add(c.apply("status", "状态")); }
            default -> { list.add(c.apply("title", "名称")); list.add(c.apply("subtitle", "说明")); list.add(c.apply("status", "状态")); }
        }
        return list;
    }

    private Map<String, Object> section(String key, String label, boolean accessible, String reason, List<Map<String, Object>> items) {
        Map<String, Object> sec = new LinkedHashMap<>();
        sec.put("key", key); sec.put("label", label); sec.put("accessible", accessible);
        sec.put("reason", reason); sec.put("items", items); sec.put("columns", columns(key)); return sec;
    }

    private Map<String, Object> sectionSql(String key, String label, String menu, long projectId, String sql, Object... args) {
        boolean ok = projectId > 0 && canView(menu, projectId);
        List<Map<String, Object>> items = ok ? jdbc.queryForList(sql, args) : List.of();
        return section(key, label, ok, ok ? null : "无权限查看该关联信息", items);
    }

    private List<Map<String, Object>> personSections(String tenant, long id, Map<String, Object> root) {
        Object org = root.get("person") instanceof Map<?, ?> p ? p.get("orgId") : null;
        long projectId = org instanceof Number n ? n.longValue() : 0;
        List<Map<String, Object>> out = new ArrayList<>();
        out.add(sectionSql("contracts", "合同", "contracts", projectId,
                "select c.id id, c.contract_no contractNo, h.house_name houseName, c.start_date startDate, c.end_date endDate, c.contract_status status, concat('/guarantee/contracts/', c.id) route from guarantee_contract c left join bp_house h on h.id=c.house_id where c.tenant_id=? and c.person_id=? and c.is_deleted=0 union all select c.id, c.contract_no, h.house_name, c.start_date, c.end_date, c.contract_status, concat('/guarantee/contracts/', c.id) from guarantee_contract_cohabitant cc join guarantee_contract c on c.id=cc.contract_id left join bp_house h on h.id=c.house_id where cc.tenant_id=? and cc.person_id=? and cc.is_deleted=0 and c.is_deleted=0", tenant, id, tenant, id));
        out.add(sectionSql("bills", "账单", "billing", projectId,
                "select b.id id, b.bill_no billNo, b.period_start periodStart, b.period_end periodEnd, b.payable_amount payableAmount, b.paid_amount paidAmount, b.bill_status status, '/guarantee/billing' route from bp_bill b where b.tenant_id=? and b.person_id=? and b.is_deleted=0 order by b.period_start desc", tenant, id));
        out.add(sectionSql("workOrders", "工单", "workOrders", projectId,
                "select o.id id, o.order_no orderNo, o.title title, o.assignee_name assigneeName, o.order_status status, '/guarantee/work-orders' route from guarantee_work_order o where o.tenant_id=? and o.person_id=? and o.is_deleted=0 order by o.id desc", tenant, id));
        out.add(sectionSql("access", "通行记录", "accessRecords", projectId,
                "select a.id id, a.valid_start validStart, a.visitor_name visitorName, a.purpose purpose, a.access_status status, '/guarantee/access' route from guarantee_access_record a where a.tenant_id=? and a.person_id=? and a.is_deleted=0 order by a.id desc", tenant, id));
        return out;
    }

    private List<Map<String, Object>> houseSections(String tenant, long id) {
        long projectId = number(jdbc.queryForList("select org_id from bp_house where tenant_id=? and id=? and is_deleted=0", tenant, id));
        List<Map<String, Object>> out = new ArrayList<>();
        out.add(sectionSql("contracts", "合同", "contracts", projectId,
                "select c.id id, c.contract_no contractNo, h.house_name houseName, c.start_date startDate, c.end_date endDate, c.contract_status status, concat('/guarantee/contracts/', c.id) route from guarantee_contract c join bp_house h on h.id=c.house_id where c.tenant_id=? and c.house_id=? and c.is_deleted=0 order by c.id desc", tenant, id));
        out.add(sectionSql("bills", "账单", "billing", projectId,
                "select b.id id, b.bill_no billNo, b.period_start periodStart, b.period_end periodEnd, b.payable_amount payableAmount, b.paid_amount paidAmount, b.bill_status status, '/guarantee/billing' route from bp_bill b where b.tenant_id=? and b.house_id=? and b.is_deleted=0 order by b.period_start desc", tenant, id));
        out.add(sectionSql("devices", "设备", "devices", projectId,
                "select d.id id, d.device_code deviceCode, d.device_name deviceName, d.device_type deviceType, d.business_status status, '/guarantee/devices' route from bp_dev_device d join bp_house h on h.space_id=d.space_id where d.tenant_id=? and h.id=? and d.is_deleted=0", tenant, id));
        out.add(sectionSql("workOrders", "工单", "workOrders", projectId,
                "select o.id id, o.order_no orderNo, o.title title, o.assignee_name assigneeName, o.order_status status, '/guarantee/work-orders' route from guarantee_work_order o where o.tenant_id=? and o.house_id=? and o.is_deleted=0 order by o.id desc", tenant, id));
        return out;
    }

    private List<Map<String, Object>> billSections(String tenant, long id) {
        long projectId = number(jdbc.queryForList("select project_id from bp_bill where tenant_id=? and id=? and is_deleted=0", tenant, id));
        List<Map<String, Object>> out = new ArrayList<>();
        out.add(sectionSql("contract", "合同", "contracts", projectId,
                "select c.id id, c.contract_no contractNo, c.contract_status contractStatus, c.start_date startDate, c.end_date endDate, concat('/guarantee/contracts/', c.id) route from bp_bill b join guarantee_contract c on c.id=b.contract_id where b.tenant_id=? and b.id=?", tenant, id));
        out.add(sectionSql("person", "人员", "person", projectId,
                "select p.id id, p.person_name personName, p.phone phone, p.person_type personType, p.status status, concat('/guarantee/persons?id=', p.id) route from bp_bill b join bp_person p on p.id=b.person_id where b.tenant_id=? and b.id=?", tenant, id));
        out.add(sectionSql("house", "房屋", "houses", projectId,
                "select h.id id, h.house_code houseCode, h.house_name houseName, h.house_status houseStatus, concat('/guarantee/houses?id=', h.id) route from bp_bill b join bp_house h on h.id=b.house_id where b.tenant_id=? and b.id=?", tenant, id));
        out.add(sectionSql("payments", "收款记录", "billing", projectId,
                "select p.id id, p.payment_no paymentNo, p.payment_method paymentMethod, p.amount amount, p.paid_time paidTime, p.payment_status status, '/guarantee/cashflow' route from bp_payment_allocation pa join bp_payment p on p.id=pa.payment_id where pa.tenant_id=? and pa.bill_id=? and p.is_deleted=0", tenant, id));
        return out;
    }

    private List<Map<String, Object>> deviceSections(String tenant, long id) {
        long projectId = number(jdbc.queryForList("select project_id from bp_dev_device where tenant_id=? and id=? and is_deleted=0", tenant, id));
        List<Map<String, Object>> out = new ArrayList<>();
        out.add(sectionSql("house", "所在房屋", "houses", projectId,
                "select h.id id, h.house_code houseCode, h.house_name houseName, h.house_status houseStatus, concat('/guarantee/houses?id=', h.id) route from bp_dev_device d join bp_house h on h.space_id=d.space_id where d.tenant_id=? and d.id=?", tenant, id));
        out.add(sectionSql("grants", "通行授权", "grants", projectId,
                "select g.id id, p.person_name personName, g.grant_level grantLevel, g.valid_start validStart, g.valid_end validEnd, g.grant_status status, '/guarantee/grants' route from bp_grant_entitlement g left join bp_person p on p.id=g.person_id where g.tenant_id=? and g.target_type='DEVICE' and g.target_id=? and g.is_deleted=0", tenant, id));
        out.add(sectionSql("alerts", "设备告警", "alertCenter", projectId,
                "select a.id id, a.title title, a.alert_level alertLevel, a.alert_status alertStatus, '/guarantee/alerts' route from guarantee_alert a where a.tenant_id=? and a.project_id=? and a.is_deleted=0 order by a.id desc", tenant, projectId));
        return out;
    }

    private List<Map<String, Object>> workOrderSections(String tenant, long id) {
        long projectId = number(jdbc.queryForList("select project_id from guarantee_work_order where tenant_id=? and id=? and is_deleted=0", tenant, id));
        List<Map<String, Object>> out = new ArrayList<>();
        out.add(sectionSql("person", "人员", "person", projectId,
                "select p.id id, p.person_name personName, p.phone phone, p.person_type personType, p.status status, concat('/guarantee/persons?id=', p.id) route from guarantee_work_order o join bp_person p on p.id=o.person_id where o.tenant_id=? and o.id=?", tenant, id));
        out.add(sectionSql("house", "房屋", "houses", projectId,
                "select h.id id, h.house_code houseCode, h.house_name houseName, h.house_status houseStatus, concat('/guarantee/houses?id=', h.id) route from guarantee_work_order o join bp_house h on h.id=o.house_id where o.tenant_id=? and o.id=?", tenant, id));
        out.add(sectionSql("contract", "合同", "contracts", projectId,
                "select c.id id, c.contract_no contractNo, c.contract_status contractStatus, c.start_date startDate, c.end_date endDate, concat('/guarantee/contracts/', c.id) route from guarantee_work_order o join guarantee_contract c on c.house_id=o.house_id where o.tenant_id=? and o.id=? and c.is_deleted=0 order by c.id desc limit 1", tenant, id));
        return out;
    }

    private List<Map<String, Object>> applicationSections(String tenant, long id) {
        long projectId = number(jdbc.queryForList("select project_id from guarantee_application where tenant_id=? and id=? and is_deleted=0", tenant, id));
        List<Map<String, Object>> out = new ArrayList<>();
        out.add(sectionSql("person", "申请人", "person", projectId,
                "select p.id id, p.person_name personName, p.phone phone, p.person_type personType, p.status status, concat('/guarantee/persons?id=', p.id) route from guarantee_application a join bp_person p on p.id=a.applicant_person_id where a.tenant_id=? and a.id=?", tenant, id));
        out.add(sectionSql("waitlist", "轮候记录", "waitlist", projectId,
                "select w.id id, w.queue_no queueNo, w.waitlist_status waitlistStatus, '/guarantee/waitlist' route from guarantee_waitlist w where w.tenant_id=? and w.application_id=? and w.is_deleted=0", tenant, id));
        out.add(sectionSql("allocation", "配租记录", "allocations", projectId,
                "select a.id id, a.allocation_no allocationNo, a.allocation_status allocationStatus, '/guarantee/allocations' route from guarantee_allocation a where a.tenant_id=? and a.application_id=? and a.is_deleted=0", tenant, id));
        out.add(sectionSql("contract", "合同", "contracts", projectId,
                "select c.id id, c.contract_no contractNo, c.contract_status contractStatus, c.start_date startDate, c.end_date endDate, concat('/guarantee/contracts/', c.id) route from guarantee_allocation a join guarantee_contract c on c.id=a.contract_id where a.tenant_id=? and a.application_id=? and c.is_deleted=0", tenant, id));
        return out;
    }

    private List<Map<String, Object>> contractSections(String tenant, long id) {
        long projectId = number(jdbc.queryForList("select project_id from guarantee_contract where tenant_id=? and id=? and is_deleted=0", tenant, id));
        List<Map<String, Object>> out = new ArrayList<>();
        out.add(sectionSql("persons", "人员", "contracts", projectId,
                "select p.id id, p.person_name personName, p.phone phone, concat('承租人') personType, p.status status, concat('/guarantee/persons?id=', p.id) route from guarantee_contract c join bp_person p on p.id=c.person_id where c.tenant_id=? and c.id=? union all select p.id, p.person_name, p.phone, concat(cc.relation_type, ' · 同住人'), p.status, concat('/guarantee/persons?id=', p.id) from guarantee_contract_cohabitant cc join bp_person p on p.id=cc.person_id where cc.tenant_id=? and cc.contract_id=? and cc.is_deleted=0", tenant, id, tenant, id));
        out.add(sectionSql("house", "房屋", "houses", projectId,
                "select h.id id, h.house_code houseCode, h.house_name houseName, h.house_status houseStatus, concat('/guarantee/houses?id=', h.id) route from guarantee_contract c join bp_house h on h.id=c.house_id where c.tenant_id=? and c.id=?", tenant, id));
        out.add(sectionSql("bills", "账单", "billing", projectId,
                "select b.id id, b.bill_no billNo, b.period_start periodStart, b.period_end periodEnd, b.payable_amount payableAmount, b.paid_amount paidAmount, b.bill_status status, '/guarantee/billing' route from bp_bill b where b.tenant_id=? and b.contract_id=? and b.is_deleted=0 order by b.period_start desc", tenant, id));
        out.add(sectionSql("deposit", "押金", "deposits", projectId,
                "select d.id id, d.amount amount, d.refunded_amount refundedAmount, d.deposit_status status, '/guarantee/deposits' route from guarantee_deposit d where d.tenant_id=? and d.contract_id=? and d.is_deleted=0", tenant, id));
        out.add(sectionSql("files", "附件", "contracts", projectId,
                "select f.id id, f.file_name fileName, f.file_size fileSize, f.create_time createTime, '/guarantee/contracts/' route from bp_file f where f.tenant_id=? and f.biz_type='CONTRACT' and f.biz_id=? and f.is_deleted=0", tenant, id));
        out.add(sectionSql("subsidies", "补贴", "subsidies", projectId,
                "select s.id id, s.subsidy_type subsidyType, s.subsidy_amount amount, s.start_date startDate, s.end_date endDate, s.subsidy_status status, '/guarantee/subsidies' route from guarantee_subsidy s where s.tenant_id=? and s.contract_id=? and s.is_deleted=0", tenant, id));
        out.add(sectionSql("changes", "变更", "contractChanges", projectId,
                "select c.id id, c.change_type changeType, c.effective_date effectiveDate, c.reason reason, c.change_status status, '/guarantee/changes' route from guarantee_contract_change c where c.tenant_id=? and c.contract_id=? and c.is_deleted=0", tenant, id));
        return out;
    }

    private long number(List<Map<String, Object>> rows) {
        if (rows.isEmpty()) return 0;
        Object v = rows.get(0).values().iterator().next();
        return v instanceof Number n ? n.longValue() : 0;
    }

    public Map<String, Object> device(long deviceId) {
        String tenant = TenantContext.require();
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select d.id, d.device_code deviceCode, d.device_name deviceName, d.project_id projectId, d.space_id spaceId "
                        + "from bp_dev_device d where d.id=? and d.tenant_id=? and d.is_deleted=0", deviceId, tenant);
        if (rows.isEmpty()) throw BizException.notFound("设备不存在");
        Map<String, Object> d = rows.get(0);
        long projectId = ((Number) d.get("projectId")).longValue();
        if (!canView("devices", projectId)) throw new BizException("BP40300", "无权查看该设备", 403);
        List<Map<String, Object>> houseRows = jdbc.queryForList(
                "select h.id, h.house_name houseName from bp_house h where h.tenant_id=? and h.space_id=? and h.is_deleted=0 limit 1",
                tenant, d.get("spaceId"));
        List<Map<String, Object>> links = new ArrayList<>();
        if (!houseRows.isEmpty()) {
            Map<String, Object> h = houseRows.get(0);
            links.add(link("HOUSE", String.valueOf(h.get("id")), "所在房屋", String.valueOf(h.get("houseName")), null,
                    "/guarantee/houses?id=" + h.get("id"), canView("houses", projectId)));
        }
        long grants = count("select count(*) from bp_grant_entitlement where tenant_id=? and target_type='DEVICE' and target_id=? and is_deleted=0", tenant, deviceId);
        links.add(link("GRANTS", null, "通行授权", canView("grants", projectId) ? grants + " 条" : "无授权查看权限",
                canView("grants", projectId) ? null : "无授权查看权限", "/guarantee/grants", canView("grants", projectId)));
        long alerts = count("select count(*) from guarantee_alert where tenant_id=? and project_id=? and is_deleted=0", tenant, projectId);
        links.add(link("ALERTS", null, "设备告警", canView("alertCenter", projectId) ? alerts + " 条" : "无告警查看权限",
                canView("alertCenter", projectId) ? null : "无告警查看权限", "/guarantee/alerts", canView("alertCenter", projectId)));
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("entity", Map.of("type", "DEVICE", "id", String.valueOf(deviceId), "title", d.get("deviceName")));
        out.put("links", links);
        return out;
    }

    public Map<String, Object> workOrder(long orderId) {
        String tenant = TenantContext.require();
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select o.id, o.order_no orderNo, o.project_id projectId, o.house_id houseId, o.person_id personId "
                        + "from guarantee_work_order o where o.id=? and o.tenant_id=? and o.is_deleted=0", orderId, tenant);
        if (rows.isEmpty()) throw BizException.notFound("工单不存在");
        Map<String, Object> o = rows.get(0);
        long projectId = ((Number) o.get("projectId")).longValue();
        if (!canView("workOrders", projectId)) throw new BizException("BP40300", "无权查看该工单", 403);
        List<Map<String, Object>> links = new ArrayList<>();
        if (o.get("personId") != null) links.add(link("PERSON", String.valueOf(o.get("personId")), "人员", "查看人员", null, "/guarantee/persons?id=" + o.get("personId"), canView("person", projectId)));
        if (o.get("houseId") != null) links.add(link("HOUSE", String.valueOf(o.get("houseId")), "房屋", "查看房源", null, "/guarantee/houses?id=" + o.get("houseId"), canView("houses", projectId)));
        if (o.get("houseId") != null) {
            List<Map<String, Object>> contracts = jdbc.queryForList(
                    "select id, contract_no contractNo from guarantee_contract where tenant_id=? and house_id=? and is_deleted=0 order by id desc limit 1",
                    tenant, o.get("houseId"));
            if (!contracts.isEmpty()) links.add(link("CONTRACT", String.valueOf(contracts.get(0).get("id")), "合同", String.valueOf(contracts.get(0).get("contractNo")), null, "/guarantee/contracts/" + contracts.get(0).get("id"), canView("contracts", projectId)));
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("entity", Map.of("type", "WORK_ORDER", "id", String.valueOf(orderId), "title", o.get("orderNo")));
        out.put("links", links);
        return out;
    }

    public Map<String, Object> application(long applicationId) {
        String tenant = TenantContext.require();
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select a.id, a.application_no applicationNo, a.project_id projectId, a.applicant_person_id personId "
                        + "from guarantee_application a where a.id=? and a.tenant_id=? and a.is_deleted=0", applicationId, tenant);
        if (rows.isEmpty()) throw BizException.notFound("申请不存在");
        Map<String, Object> a = rows.get(0);
        long projectId = ((Number) a.get("projectId")).longValue();
        if (!canView("applications", projectId)) throw new BizException("BP40300", "无权查看该申请", 403);
        List<Map<String, Object>> links = new ArrayList<>();
        if (a.get("personId") != null) links.add(link("PERSON", String.valueOf(a.get("personId")), "申请人", "查看人员", null, "/guarantee/persons?id=" + a.get("personId"), canView("person", projectId)));
        long waitlists = count("select count(*) from guarantee_waitlist where tenant_id=? and application_id=? and is_deleted=0", tenant, applicationId);
        links.add(link("WAITLIST", null, "轮候记录", waitlists + " 条", null, "/guarantee/waitlist", canView("waitlist", projectId)));
        long allocations = count("select count(*) from guarantee_allocation where tenant_id=? and application_id=? and is_deleted=0", tenant, applicationId);
        links.add(link("ALLOCATION", null, "配租记录", allocations + " 条", null, "/guarantee/allocations", canView("allocations", projectId)));
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("entity", Map.of("type", "APPLICATION", "id", String.valueOf(applicationId), "title", a.get("applicationNo")));
        out.put("links", links);
        return out;
    }

    public Map<String, Object> house(long houseId) {
        String tenant = TenantContext.require();
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select h.id, h.house_name houseName, h.house_code houseCode, h.org_id projectId, h.house_status houseStatus "
                        + "from bp_house h where h.id=? and h.tenant_id=? and h.is_deleted=0", houseId, tenant);
        if (rows.isEmpty()) throw BizException.notFound("房源不存在");
        Map<String, Object> h = rows.get(0);
        long projectId = ((Number) h.get("projectId")).longValue();
        if (!canView("houses", projectId)) throw new BizException("BP40300", "无权查看该房源", 403);
        long contracts = count("select count(*) from guarantee_contract where tenant_id=? and house_id=? and is_deleted=0", tenant, houseId);
        long bills = count("select count(*) from bp_bill where tenant_id=? and house_id=? and is_deleted=0", tenant, houseId);
        long devices = count("select count(*) from bp_dev_device where tenant_id=? and space_id in (select id from bp_space where tenant_id=? and org_id=?) and is_deleted=0", tenant, tenant, projectId);
        long workOrders = count("select count(*) from guarantee_work_order where tenant_id=? and house_id=? and is_deleted=0", tenant, houseId);
        List<Map<String, Object>> links = new ArrayList<>();
        links.add(link("CONTRACTS", null, "合同", canView("contracts", projectId) ? contracts + " 份" : "无合同查看权限", canView("contracts", projectId) ? null : "无合同查看权限", "/guarantee/contracts", canView("contracts", projectId)));
        links.add(link("BILLS", null, "账单", canView("billing", projectId) ? bills + " 笔" : "无账单查看权限", canView("billing", projectId) ? null : "无账单查看权限", "/guarantee/billing", canView("billing", projectId)));
        links.add(link("DEVICES", null, "设备", canView("devices", projectId) ? devices + " 台" : "无设备查看权限", canView("devices", projectId) ? null : "无设备查看权限", "/guarantee/devices", canView("devices", projectId)));
        links.add(link("WORK_ORDERS", null, "工单", canView("workOrders", projectId) ? workOrders + " 个" : "无工单查看权限", canView("workOrders", projectId) ? null : "无工单查看权限", "/guarantee/work-orders", canView("workOrders", projectId)));
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("entity", Map.of("type", "HOUSE", "id", String.valueOf(houseId), "title", h.get("houseName")));
        out.put("links", links);
        return out;
    }

    public Map<String, Object> bill(long billId) {
        String tenant = TenantContext.require();
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select b.id, b.bill_no billNo, b.project_id projectId, b.contract_id contractId, b.house_id houseId, b.person_id personId "
                        + "from bp_bill b where b.id=? and b.tenant_id=? and b.is_deleted=0", billId, tenant);
        if (rows.isEmpty()) throw BizException.notFound("账单不存在");
        Map<String, Object> b = rows.get(0);
        long projectId = ((Number) b.get("projectId")).longValue();
        if (!canView("billing", projectId)) throw new BizException("BP40300", "无权查看该账单", 403);
        List<Map<String, Object>> links = new ArrayList<>();
        if (b.get("contractId") != null) links.add(link("CONTRACT", String.valueOf(b.get("contractId")), "合同", "查看合同", null, "/guarantee/contracts/" + b.get("contractId"), canView("contracts", projectId)));
        if (b.get("personId") != null) links.add(link("PERSON", String.valueOf(b.get("personId")), "人员", "查看人员", null, "/guarantee/persons?id=" + b.get("personId"), canView("person", projectId)));
        if (b.get("houseId") != null) links.add(link("HOUSE", String.valueOf(b.get("houseId")), "房屋", "查看房源", null, "/guarantee/houses?id=" + b.get("houseId"), canView("houses", projectId)));
        long payments = count("select count(*) from bp_payment_allocation pa join bp_payment p on p.id=pa.payment_id where pa.bill_id=? and p.tenant_id=? and p.is_deleted=0", billId, tenant);
        links.add(link("PAYMENTS", null, "收款记录", canView("billing", projectId) ? payments + " 笔" : "无收款查看权限", canView("billing", projectId) ? null : "无收款查看权限", "/guarantee/cashflow", canView("billing", projectId)));
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("entity", Map.of("type", "BILL", "id", String.valueOf(billId), "title", b.get("billNo")));
        out.put("links", links);
        return out;
    }

    private long count(String sql, Object... args) {
        Long n = jdbc.queryForObject(sql, Long.class, args);
        return n == null ? 0 : n;
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
