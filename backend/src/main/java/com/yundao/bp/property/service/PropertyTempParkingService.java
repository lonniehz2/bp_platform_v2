package com.yundao.bp.property.service;

import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.sql.Date;
import java.sql.Timestamp;
import java.time.Duration;
import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** 临时停车入场、出场计费与缴费。 */
@Service
public class PropertyTempParkingService {

    private final JdbcTemplate jdbc;
    private final SnowflakeIdGenerator idGen;
    private final PropertyBillingService billingService;

    public PropertyTempParkingService(JdbcTemplate jdbc, SnowflakeIdGenerator idGen,
                                      PropertyBillingService billingService) {
        this.jdbc = jdbc;
        this.idGen = idGen;
        this.billingService = billingService;
    }

    public List<Map<String, Object>> list(Long projectId, String status) {
        requireProject(projectId);
        return jdbc.queryForList(
                "select id, plate_no plateNo, entry_time entryTime, exit_time exitTime, hours, "
                        + "hourly_rate hourlyRate, amount, bill_id billId, pay_method payMethod, status "
                        + "from prop_temp_parking where tenant_id=? and project_id=? "
                        + "and (? is null or status=?) order by id desc limit 200",
                TenantContext.tenantId(), projectId, status, status);
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> entry(Long projectId, EntryCmd cmd) {
        requireProject(projectId);
        if (cmd.plateNo() == null || cmd.plateNo().isBlank()) {
            throw BizException.paramInvalid("车牌号不能为空");
        }
        long id = idGen.nextId();
        jdbc.update("insert into prop_temp_parking(id,tenant_id,project_id,plate_no,parking_space_id,"
                        + "entry_time,status,create_by,create_time,update_time) "
                        + "values(?,?,?,?,?,?, 'IN',?,now(),now())",
                id, TenantContext.tenantId(), projectId, cmd.plateNo().trim(),
                cmd.parkingSpaceId(), Timestamp.valueOf(cmd.entryTime() == null
                        ? LocalDateTime.now() : cmd.entryTime()),
                String.valueOf(TenantContext.userId()));
        return Map.of("id", id);
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> exit(Long projectId, Long id, LocalDateTime exitTime) {
        requireProject(projectId);
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select * from prop_temp_parking where id=? and tenant_id=? and project_id=? and status='IN'",
                id, TenantContext.tenantId(), projectId);
        if (rows.isEmpty()) throw BizException.stateConflict("临时停车记录不存在或已出场");
        Map<String, Object> r = rows.get(0);
        Object entryValue = r.get("entry_time");
        LocalDateTime entry = entryValue instanceof Timestamp ts
                ? ts.toLocalDateTime() : (LocalDateTime) entryValue;
        LocalDateTime exit = exitTime == null ? LocalDateTime.now() : exitTime;
        if (exit.isBefore(entry)) throw BizException.paramInvalid("出场时间不能早于入场时间");
        long minutes = Math.max(1, Duration.between(entry, exit).toMinutes());
        BigDecimal hours = BigDecimal.valueOf(minutes)
                .divide(BigDecimal.valueOf(60), 2, RoundingMode.CEILING).max(BigDecimal.ONE);
        List<Map<String, Object>> rates = jdbc.queryForList(
                "select price from prop_parking_rate where tenant_id=? and project_id=? "
                        + "and fee_type='TEMP' and billing_cycle='HOUR' and status='ENABLED' "
                        + "and is_deleted=0 order by effective_from desc limit 1",
                TenantContext.tenantId(), projectId);
        BigDecimal rate = rates.isEmpty() ? BigDecimal.ZERO : (BigDecimal) rates.get(0).get("price");
        BigDecimal amount = hours.multiply(rate).setScale(2, RoundingMode.HALF_UP);
        Map<String, Object> fee = jdbc.queryForMap(
                "select id, income_category, income_subcategory from prop_fee_item "
                        + "where tenant_id=? and project_id=? and fee_item_code='TEMP_PARKING' and is_deleted=0",
                TenantContext.tenantId(), projectId);
        long billId = idGen.nextId();
        String billNo = "PB" + billId;
        Date periodStart = Date.valueOf(entry.toLocalDate());
        Date periodEnd = Date.valueOf(exit.toLocalDate());
        jdbc.update("insert into prop_bill(id,tenant_id,project_id,bill_no,income_category,income_subcategory,"
                        + "fee_item_id,payer_type,payer_name,period_start,period_end,quantity,unit_price,"
                        + "bill_amount,payable_amount,bill_status,due_date,source_type,source_id,"
                        + "service_start_date,service_end_date,is_deleted,create_by,create_time,update_by,update_time) "
                        + "values(?,?,?,?,?,?,?, 'OTHER',?,?,?,?,?,?,?, 'PENDING',?, 'TEMP_PARKING',?,?,?,0,?,now(),?,now())",
                billId, TenantContext.tenantId(), projectId, billNo,
                fee.get("income_category"), fee.get("income_subcategory"), fee.get("id"),
                r.get("plate_no"), periodStart, periodEnd, hours, rate, amount, amount,
                periodEnd, id, periodStart, periodEnd,
                String.valueOf(TenantContext.userId()), String.valueOf(TenantContext.userId()));
        jdbc.update("update prop_temp_parking set exit_time=?, hours=?, hourly_rate=?, amount=?, "
                        + "bill_id=?, status='OUT', update_time=now() where id=?",
                Timestamp.valueOf(exit), hours, rate, amount, billId, id);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", id);
        out.put("billId", billId);
        out.put("hours", hours);
        out.put("amount", amount);
        return out;
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> pay(Long projectId, Long id, String payMethod) {
        requireProject(projectId);
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select amount, bill_id from prop_temp_parking where id=? and tenant_id=? "
                        + "and project_id=? and status='OUT'",
                id, TenantContext.tenantId(), projectId);
        if (rows.isEmpty()) throw BizException.stateConflict("临时停车记录未出场或已缴费");
        BigDecimal amount = (BigDecimal) rows.get(0).get("amount");
        Long billId = ((Number) rows.get(0).get("bill_id")).longValue();
        billingService.pay(new PropertyBillingService.PayCmd(projectId, List.of(billId),
                amount, payMethod == null ? "CASH" : payMethod, "临时停车费"));
        jdbc.update("update prop_temp_parking set status='PAID', pay_method=?, update_time=now() where id=?",
                payMethod == null ? "CASH" : payMethod, id);
        return Map.of("id", id, "amount", amount, "status", "PAID");
    }

    private void requireProject(Long projectId) {
        if (projectId == null) throw BizException.paramInvalid("请选择项目");
        Long n = jdbc.queryForObject("select count(*) from prop_project_config "
                        + "where tenant_id=? and org_id=? and is_deleted=0",
                Long.class, TenantContext.tenantId(), projectId);
        if (n == null || n == 0) throw BizException.notFound("物业项目");
    }

    public record EntryCmd(String plateNo, Long parkingSpaceId, LocalDateTime entryTime) {
    }
}
