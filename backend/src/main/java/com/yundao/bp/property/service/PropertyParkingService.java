package com.yundao.bp.property.service;

import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import java.math.BigDecimal;
import java.sql.Date;
import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** 车位：车位档案、包月/包年价格、计费方案、退租核算。 */
@Service
public class PropertyParkingService {

    private final JdbcTemplate jdbc;
    private final SnowflakeIdGenerator idGen;

    public PropertyParkingService(JdbcTemplate jdbc, SnowflakeIdGenerator idGen) {
        this.jdbc = jdbc;
        this.idGen = idGen;
    }

    public List<Map<String, Object>> spaces(Long projectId) {
        requireProject(projectId);
        return jdbc.queryForList(
                "select s.id, s.garage_name garageName, s.space_no spaceNo, s.space_type spaceType, "
                        + "s.area, s.status, p.id planId, p.billing_cycle billingCycle, "
                        + "p.unit_price unitPrice, p.start_date startDate, p.end_date endDate, "
                        + "p.plan_status planStatus, b.bill_status billStatus, b.id billId "
                        + "from prop_parking_space s "
                        + "left join prop_parking_plan p on p.parking_space_id=s.id and p.plan_status='ACTIVE' "
                        + "left join prop_bill b on b.id=p.bill_id and b.is_deleted=0 "
                        + "where s.tenant_id=? and s.project_id=? and s.is_deleted=0 order by s.space_no",
                TenantContext.tenantId(), projectId);
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> createSpace(Long projectId, SpaceCmd cmd) {
        requireProject(projectId);
        if (cmd.spaceNo() == null || cmd.spaceNo().isBlank()) {
            throw BizException.paramInvalid("车位编号不能为空");
        }
        Long dup = jdbc.queryForObject("select count(*) from prop_parking_space "
                        + "where tenant_id=? and project_id=? and garage_name=? and space_no=? and is_deleted=0",
                Long.class, TenantContext.tenantId(), projectId,
                cmd.garageName() == null ? "默认车库" : cmd.garageName(), cmd.spaceNo().trim());
        if (dup != null && dup > 0) {
            throw BizException.stateConflict("车位编号已存在");
        }
        long id = idGen.nextId();
        jdbc.update("insert into prop_parking_space(id,tenant_id,project_id,garage_name,space_no,"
                        + "space_type,area,owner_person_id,status,is_deleted,create_by,create_time,update_by,update_time) "
                        + "values(?,?,?,?,?,?,?,?, 'ENABLED',0,?,now(),?,now())",
                id, TenantContext.tenantId(), projectId,
                cmd.garageName() == null || cmd.garageName().isBlank() ? "默认车库" : cmd.garageName().trim(),
                cmd.spaceNo().trim(), cmd.spaceType() == null ? "STANDARD" : cmd.spaceType(),
                cmd.area(), cmd.ownerPersonId(),
                String.valueOf(TenantContext.userId()), String.valueOf(TenantContext.userId()));
        return Map.of("id", id);
    }

    public List<Map<String, Object>> rates(Long projectId) {
        requireProject(projectId);
        return jdbc.queryForList(
                "select id, garage_name garageName, space_type spaceType, fee_type feeType, "
                        + "billing_cycle billingCycle, price, effective_from effectiveFrom, status "
                        + "from prop_parking_rate where tenant_id=? and project_id=? and is_deleted=0 "
                        + "order by fee_type, billing_cycle", TenantContext.tenantId(), projectId);
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> createRate(Long projectId, RateCmd cmd) {
        requireProject(projectId);
        if (cmd.price() == null || cmd.price().compareTo(BigDecimal.ZERO) < 0) {
            throw BizException.paramInvalid("周期价格不合法");
        }
        long id = idGen.nextId();
        jdbc.update("insert into prop_parking_rate(id,tenant_id,project_id,garage_name,space_type,"
                        + "fee_type,billing_cycle,price,effective_from,status,is_deleted,create_time,update_time) "
                        + "values(?,?,?,?,?,?,?,?,?, 'ENABLED',0,now(),now())",
                id, TenantContext.tenantId(), projectId,
                cmd.garageName(), cmd.spaceType() == null ? "STANDARD" : cmd.spaceType(),
                cmd.feeType() == null ? "MANAGEMENT" : cmd.feeType(), cmd.billingCycle(),
                cmd.price(), Date.valueOf(cmd.effectiveFrom() == null ? LocalDate.now() : cmd.effectiveFrom()));
        return Map.of("id", id);
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> createPlan(PlanCmd cmd) {
        requireProject(cmd.projectId());
        Map<String, Object> space = getSpace(cmd.projectId(), cmd.parkingSpaceId());
        String feeType = cmd.feeType() == null ? "MANAGEMENT" : cmd.feeType();
        String cycle = cmd.billingCycle();
        if (!List.of("MONTH", "QUARTER", "HALF_YEAR", "YEAR").contains(cycle)) {
            throw BizException.paramInvalid("车位计费周期不合法");
        }
        BigDecimal price = findRate(cmd.projectId(), space.get("garage_name"), space.get("space_type"),
                feeType, cycle);
        LocalDate start = cmd.startDate() == null ? LocalDate.now() : cmd.startDate();
        LocalDate end = endOf(start, cycle);
        Map<String, Object> feeItem = jdbc.queryForMap(
                "select id, income_category, income_subcategory from prop_fee_item "
                        + "where tenant_id=? and project_id=? and fee_item_code=? and is_deleted=0",
                TenantContext.tenantId(), cmd.projectId(),
                "RENT".equals(feeType) ? "PARKING_RENT" : "PARKING_MGMT");
        long planId = idGen.nextId();
        long billId = idGen.nextId();
        String billNo = "PB" + billId;
        Long owner = cmd.ownerPersonId() == null ? null : cmd.ownerPersonId();
        String payerName = space.get("space_no") + " 车位" +
                ("RENT".equals(feeType) ? "租赁费" : "管理费");
        jdbc.update("insert into prop_parking_plan(id,tenant_id,project_id,parking_space_id,owner_person_id,"
                        + "fee_type,billing_cycle,unit_price,start_date,end_date,next_due_date,bill_id,"
                        + "plan_status,create_time,update_time) values(?,?,?,?,?,?,?,?,?,?,?,?, 'ACTIVE',now(),now())",
                planId, TenantContext.tenantId(), cmd.projectId(), cmd.parkingSpaceId(), owner,
                feeType, cycle, price, Date.valueOf(start), Date.valueOf(end), Date.valueOf(end), billId);
        jdbc.update("insert into prop_bill(id,tenant_id,project_id,bill_no,income_category,"
                        + "income_subcategory,fee_item_id,payer_type,payer_person_id,payer_name,"
                        + "parking_space_id,period_start,period_end,billing_cycle,cycle_count,quantity,"
                        + "unit_price,bill_amount,payable_amount,bill_status,due_date,source_type,source_id,"
                        + "service_start_date,service_end_date,is_deleted,create_by,create_time,update_by,update_time) "
                        + "values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,1,1,?,?,?, 'PENDING',?, 'PARKING_PLAN',?,?,?,0,?,now(),?,now())",
                billId, TenantContext.tenantId(), cmd.projectId(), billNo,
                feeItem.get("income_category"), feeItem.get("income_subcategory"), feeItem.get("id"),
                "PARKING", owner, payerName, cmd.parkingSpaceId(),
                Date.valueOf(start), Date.valueOf(end), cycle, price, price, price,
                Date.valueOf(end), planId, Date.valueOf(start), Date.valueOf(end),
                String.valueOf(TenantContext.userId()), String.valueOf(TenantContext.userId()));
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("planId", planId);
        out.put("billId", billId);
        out.put("amount", price);
        out.put("startDate", start);
        out.put("endDate", end);
        return out;
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> terminate(Long planId, LocalDate terminationDate) {
        List<Map<String, Object>> plans = jdbc.queryForList(
                "select * from prop_parking_plan where id=? and tenant_id=? and plan_status='ACTIVE'",
                planId, TenantContext.tenantId());
        if (plans.isEmpty()) {
            throw BizException.notFound("车位方案");
        }
        Map<String, Object> p = plans.get(0);
        LocalDate start = ((Date) p.get("start_date")).toLocalDate();
        LocalDate end = ((Date) p.get("end_date")).toLocalDate();
        LocalDate stop = terminationDate == null ? LocalDate.now() : terminationDate;
        if (stop.isBefore(start)) stop = start;
        if (stop.isAfter(end)) stop = end;
        BigDecimal annual = (BigDecimal) p.get("unit_price");
        String cycle = String.valueOf(p.get("billing_cycle"));
        int used = usedMonths(start, stop);
        Map<String, Object> space = getSpace(((Number) p.get("project_id")).longValue(),
                ((Number) p.get("parking_space_id")).longValue());
        BigDecimal monthly = findRate(((Number) p.get("project_id")).longValue(),
                space.get("garage_name"), space.get("space_type"),
                String.valueOf(p.get("fee_type")), "MONTH");
        BigDecimal refund = BigDecimal.ZERO;
        if ("YEAR".equals(cycle)) {
            refund = annual.subtract(monthly.multiply(BigDecimal.valueOf(used))).max(BigDecimal.ZERO);
        }
        BigDecimal paid = BigDecimal.ZERO;
        Object billId = p.get("bill_id");
        if (billId != null) {
            List<Map<String, Object>> bills = jdbc.queryForList(
                    "select paid_amount, bill_status from prop_bill where id=?", billId);
            if (!bills.isEmpty()) {
                paid = (BigDecimal) bills.get(0).get("paid_amount");
                if ("PENDING".equals(bills.get(0).get("bill_status"))) {
                    jdbc.update("update prop_bill set bill_status='CANCELLED', update_time=now() where id=?", billId);
                }
            }
        }
        jdbc.update("update prop_parking_plan set plan_status='TERMINATED', termination_date=?, "
                        + "refund_amount=?, update_time=now() where id=?",
                Date.valueOf(stop), refund, planId);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("usedMonths", used);
        out.put("annualPrice", annual);
        out.put("monthlyPrice", monthly);
        out.put("paidAmount", paid);
        out.put("refundAmount", refund);
        out.put("terminationDate", stop);
        return out;
    }

    private Map<String, Object> getSpace(Long projectId, Long spaceId) {
        List<Map<String, Object>> list = jdbc.queryForList(
                "select * from prop_parking_space where id=? and tenant_id=? and project_id=? and is_deleted=0",
                spaceId, TenantContext.tenantId(), projectId);
        if (list.isEmpty()) throw BizException.notFound("车位");
        return list.get(0);
    }

    private BigDecimal findRate(Long projectId, Object garage, Object spaceType,
                                String feeType, String cycle) {
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select price from prop_parking_rate where tenant_id=? and project_id=? "
                        + "and (garage_name is null or garage_name=?) and (space_type is null or space_type=?) "
                        + "and fee_type=? and billing_cycle=? and status='ENABLED' "
                        + "and effective_from <= curdate() and (effective_to is null or effective_to >= curdate()) "
                        + "order by id desc limit 1",
                TenantContext.tenantId(), projectId, garage, spaceType, feeType, cycle);
        if (rows.isEmpty()) {
            throw BizException.stateConflict("未配置该车位类型的" + cycle + "价格");
        }
        return (BigDecimal) rows.get(0).get("price");
    }

    private void requireProject(Long projectId) {
        if (projectId == null) throw BizException.paramInvalid("请选择项目");
        Long n = jdbc.queryForObject("select count(*) from prop_project_config "
                        + "where tenant_id=? and org_id=? and is_deleted=0",
                Long.class, TenantContext.tenantId(), projectId);
        if (n == null || n == 0) throw BizException.notFound("物业项目");
    }

    private static LocalDate endOf(LocalDate start, String cycle) {
        return switch (cycle) {
            case "MONTH" -> start.plusMonths(1).minusDays(1);
            case "QUARTER" -> start.plusMonths(3).minusDays(1);
            case "HALF_YEAR" -> start.plusMonths(6).minusDays(1);
            case "YEAR" -> start.plusMonths(12).minusDays(1);
            default -> start;
        };
    }

    private static int usedMonths(LocalDate start, LocalDate end) {
        int months = (int) ChronoUnit.MONTHS.between(start.withDayOfMonth(1), end.withDayOfMonth(1)) + 1;
        return Math.max(1, Math.min(months, 12));
    }

    public record SpaceCmd(String garageName, String spaceNo, String spaceType,
                           BigDecimal area, Long ownerPersonId) {
    }

    public record RateCmd(String garageName, String spaceType, String feeType,
                          String billingCycle, BigDecimal price, LocalDate effectiveFrom) {
    }

    public record PlanCmd(Long projectId, Long parkingSpaceId, Long ownerPersonId,
                          String feeType, String billingCycle, LocalDate startDate) {
    }
}
