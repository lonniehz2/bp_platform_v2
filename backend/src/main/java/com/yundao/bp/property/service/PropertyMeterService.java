package com.yundao.bp.property.service;

import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.sql.Date;
import java.time.LocalDate;
import java.time.YearMonth;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** 物业水电表与抄表出账。 */
@Service
public class PropertyMeterService {

    private final JdbcTemplate jdbc;
    private final SnowflakeIdGenerator idGen;

    public PropertyMeterService(JdbcTemplate jdbc, SnowflakeIdGenerator idGen) {
        this.jdbc = jdbc;
        this.idGen = idGen;
    }

    public List<Map<String, Object>> meters(Long projectId) {
        requireProject(projectId);
        return jdbc.queryForList(
                "select m.id, m.house_id houseId, h.house_name houseName, m.meter_type meterType, "
                        + "m.meter_no meterNo, m.device_id deviceId, m.multiplier, m.unit_price unitPrice, "
                        + "m.initial_reading initialReading, m.status, "
                        + "(select r.current_reading from prop_meter_reading r where r.meter_id=m.id "
                        + " order by r.id desc limit 1) lastReading "
                        + "from prop_meter m left join bp_asset_house h on h.id=m.house_id "
                        + "where m.tenant_id=? and m.project_id=? and m.is_deleted=0 order by m.meter_no",
                TenantContext.tenantId(), projectId);
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> createMeter(Long projectId, MeterCmd cmd) {
        requireProject(projectId);
        requireHouse(projectId, cmd.houseId());
        if (cmd.meterNo() == null || cmd.meterNo().isBlank()) {
            throw BizException.paramInvalid("表号不能为空");
        }
        String type = cmd.meterType() == null ? "WATER" : cmd.meterType();
        if (!List.of("WATER", "ELECTRICITY").contains(type)) {
            throw BizException.paramInvalid("表类型不合法");
        }
        long id = idGen.nextId();
        jdbc.update("insert into prop_meter(id,tenant_id,project_id,house_id,meter_type,meter_no,device_id,"
                        + "multiplier,unit_price,initial_reading,status,is_deleted,create_by,create_time,update_by,update_time) "
                        + "values(?,?,?,?,?,?,?,?,?,?, 'ENABLED',0,?,now(),?,now())",
                id, TenantContext.tenantId(), projectId, cmd.houseId(), type, cmd.meterNo().trim(),
                cmd.deviceId(), cmd.multiplier() == null ? BigDecimal.ONE : cmd.multiplier(),
                cmd.unitPrice() == null ? BigDecimal.ZERO : cmd.unitPrice(),
                cmd.initialReading() == null ? BigDecimal.ZERO : cmd.initialReading(),
                String.valueOf(TenantContext.userId()), String.valueOf(TenantContext.userId()));
        return Map.of("id", id);
    }

    public List<Map<String, Object>> readings(Long projectId, Long meterId) {
        requireProject(projectId);
        return jdbc.queryForList(
                "select r.id, r.meter_id meterId, m.meter_no meterNo, m.meter_type meterType, "
                        + "r.period, r.prev_reading prevReading, r.current_reading currentReading, "
                        + "r.usage_amount usageAmount, r.amount, r.bill_id billId, r.read_date readDate, "
                        + "r.status from prop_meter_reading r join prop_meter m on m.id=r.meter_id "
                        + "where r.tenant_id=? and r.project_id=? and (? is null or r.meter_id=?) "
                        + "order by r.id desc limit 200",
                TenantContext.tenantId(), projectId, meterId, meterId);
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> addReading(Long projectId, ReadingCmd cmd) {
        requireProject(projectId);
        List<Map<String, Object>> meters = jdbc.queryForList(
                "select * from prop_meter where id=? and tenant_id=? and project_id=? and is_deleted=0",
                cmd.meterId(), TenantContext.tenantId(), projectId);
        if (meters.isEmpty()) throw BizException.notFound("水表/电表");
        Map<String, Object> m = meters.get(0);
        String period = cmd.period();
        if (period == null || !period.matches("\\d{4}-\\d{2}")) {
            throw BizException.paramInvalid("抄表期间格式应为 yyyy-MM");
        }
        Long dup = jdbc.queryForObject("select count(*) from prop_meter_reading "
                        + "where tenant_id=? and meter_id=? and period=?",
                Long.class, TenantContext.tenantId(), cmd.meterId(), period);
        if (dup != null && dup > 0) throw BizException.stateConflict("该表本期已抄表");
        BigDecimal current = cmd.currentReading();
        if (current == null) throw BizException.paramInvalid("本期读数不能为空");
        List<Map<String, Object>> last = jdbc.queryForList(
                "select current_reading from prop_meter_reading where meter_id=? order by id desc limit 1",
                cmd.meterId());
        BigDecimal prev = last.isEmpty() ? (BigDecimal) m.get("initial_reading")
                : (BigDecimal) last.get(0).get("current_reading");
        if (current.compareTo(prev) < 0) throw BizException.paramInvalid("本期读数不能小于上期读数");
        BigDecimal multiplier = (BigDecimal) m.get("multiplier");
        BigDecimal usage = current.subtract(prev).multiply(multiplier).setScale(2, RoundingMode.HALF_UP);
        BigDecimal price = (BigDecimal) m.get("unit_price");
        BigDecimal amount = usage.multiply(price).setScale(2, RoundingMode.HALF_UP);
        String type = String.valueOf(m.get("meter_type"));
        String feeCode = "WATER".equals(type) ? "WATER" : "ELECTRICITY";
        Map<String, Object> fee = jdbc.queryForMap(
                "select id, income_category, income_subcategory from prop_fee_item "
                        + "where tenant_id=? and project_id=? and fee_item_code=? and is_deleted=0",
                TenantContext.tenantId(), projectId, feeCode);
        Long owner = jdbc.queryForObject(
                "select coalesce((select ou.person_id from prop_owner_unit ou where ou.house_id=? "
                        + "and ou.is_primary=1 and ou.status='ACTIVE' and ou.is_deleted=0 limit 1), null)",
                Long.class, m.get("house_id"));
        long readingId = idGen.nextId();
        long billId = idGen.nextId();
        LocalDate first = YearMonth.parse(period).atDay(1);
        LocalDate lastDay = YearMonth.parse(period).atEndOfMonth();
        String billNo = "PB" + billId;
        jdbc.update("insert into prop_meter_reading(id,tenant_id,project_id,meter_id,period,prev_reading,"
                        + "current_reading,usage_amount,unit_price,amount,bill_id,read_date,status,"
                        + "create_by,create_time) values(?,?,?,?,?,?,?,?,?,?,?,?, 'BILLED',?,now())",
                readingId, TenantContext.tenantId(), projectId, cmd.meterId(), period, prev, current,
                usage, price, amount, billId,
                Date.valueOf(cmd.readDate() == null ? LocalDate.now() : cmd.readDate()),
                String.valueOf(TenantContext.userId()));
        String payerName = String.valueOf(m.get("meter_no"));
        jdbc.update("insert into prop_bill(id,tenant_id,project_id,bill_no,income_category,income_subcategory,"
                        + "fee_item_id,payer_type,payer_person_id,payer_name,house_id,period_start,period_end,"
                        + "billing_cycle,cycle_count,quantity,unit_price,bill_amount,payable_amount,bill_status,"
                        + "due_date,source_type,source_id,service_start_date,service_end_date,is_deleted,"
                        + "create_by,create_time,update_by,update_time) "
                        + "values(?,?,?,?,?,?,?,?,?,?,?,?,?, 'MONTH',1,?,?,?,?, 'PENDING',?, 'METER',?,?,?,0,?,now(),?,now())",
                billId, TenantContext.tenantId(), projectId, billNo,
                fee.get("income_category"), fee.get("income_subcategory"), fee.get("id"),
                owner == null ? "HOUSE" : "OWNER", owner, payerName, m.get("house_id"),
                Date.valueOf(first), Date.valueOf(lastDay),
                usage, price, amount, amount, Date.valueOf(lastDay), readingId,
                Date.valueOf(first), Date.valueOf(lastDay),
                String.valueOf(TenantContext.userId()), String.valueOf(TenantContext.userId()));
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("readingId", readingId);
        out.put("billId", billId);
        out.put("usage", usage);
        out.put("amount", amount);
        return out;
    }

    private void requireProject(Long projectId) {
        if (projectId == null) throw BizException.paramInvalid("请选择项目");
        Long n = jdbc.queryForObject("select count(*) from prop_project_config "
                        + "where tenant_id=? and org_id=? and is_deleted=0",
                Long.class, TenantContext.tenantId(), projectId);
        if (n == null || n == 0) throw BizException.notFound("物业项目");
    }

    private void requireHouse(Long projectId, Long houseId) {
        if (houseId == null) throw BizException.paramInvalid("请选择房屋");
        Long n = jdbc.queryForObject("select count(*) from bp_asset_house "
                        + "where id=? and tenant_id=? and org_id=? and is_deleted=0",
                Long.class, houseId, TenantContext.tenantId(), projectId);
        if (n == null || n == 0) throw BizException.notFound("物业房屋");
    }

    public record MeterCmd(Long houseId, String meterType, String meterNo, String deviceId,
                           BigDecimal multiplier, BigDecimal unitPrice, BigDecimal initialReading) {
    }

    public record ReadingCmd(Long meterId, String period, BigDecimal currentReading, LocalDate readDate) {
    }
}
