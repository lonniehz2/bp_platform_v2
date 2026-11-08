package com.yundao.platform.service;

import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.id.IdGenerator;
import com.yundao.platform.common.tenant.TenantContext;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class MeterService {

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;

    public MeterService(JdbcTemplate jdbc, IdGenerator idGen) {
        this.jdbc = jdbc;
        this.idGen = idGen;
    }

    public List<Map<String, Object>> meters(long projectId) {
        return jdbc.queryForList(
                "select m.id, m.project_id projectId, m.house_id houseId, h.house_name houseName, "
                        + "m.meter_type meterType, m.meter_no meterNo, m.initial_reading initialReading, "
                        + "m.current_reading currentReading, m.install_date installDate, m.meter_status meterStatus "
                        + "from guarantee_meter m left join bp_house h on h.id=m.house_id "
                        + "where m.tenant_id=? and m.project_id=? and m.is_deleted=0 order by m.id desc",
                TenantContext.require(), projectId);
    }

    public Map<String, Object> create(MeterCmd cmd) {
        String tenant = TenantContext.require();
        if (cmd.projectId() == null || cmd.houseId() == null || cmd.meterNo() == null
                || cmd.meterNo().isBlank() || cmd.meterType() == null) {
            throw BizException.param("项目、房屋、表类型、表号不能为空");
        }
        if (!List.of("WATER", "ELECTRICITY", "GAS").contains(cmd.meterType())) {
            throw BizException.param("表类型不合法");
        }
        if (count("select count(*) from bp_house where id=? and tenant_id=? and org_id=? and is_deleted=0",
                cmd.houseId(), tenant, cmd.projectId()) == 0) {
            throw BizException.param("房屋不属于当前项目");
        }
        BigDecimal initial = cmd.initialReading() == null ? BigDecimal.ZERO : cmd.initialReading();
        long id = idGen.nextId();
        try {
            jdbc.update("insert into guarantee_meter(id,tenant_id,project_id,house_id,meter_type,meter_no,"
                            + "initial_reading,current_reading,install_date,meter_status,is_deleted) "
                            + "values(?,?,?,?,?,?,?,?,?, 'ACTIVE',0)",
                    id, tenant, cmd.projectId(), cmd.houseId(), cmd.meterType(), cmd.meterNo().trim(),
                    initial, initial, cmd.installDate());
        } catch (DataIntegrityViolationException e) {
            throw BizException.conflict("表号已存在");
        }
        return Map.of("id", id, "meterNo", cmd.meterNo(), "meterType", cmd.meterType());
    }

    public List<Map<String, Object>> readings(long meterId) {
        return jdbc.queryForList(
                "select id, meter_id meterId, reading_date readingDate, reading_value readingValue, "
                        + "previous_value previousValue, usage_amount usageAmount, reader_name readerName, "
                        + "create_time createTime from guarantee_meter_reading "
                        + "where tenant_id=? and meter_id=? order by reading_date desc, id desc",
                TenantContext.require(), meterId);
    }

    public Map<String, Object> read(long meterId, ReadingCmd cmd) {
        String tenant = TenantContext.require();
        if (cmd.readingValue() == null || cmd.readingValue().signum() < 0) {
            throw BizException.param("抄表读数不能为空或负数");
        }
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select current_reading currentReading from guarantee_meter "
                        + "where id=? and tenant_id=? and is_deleted=0 for update", meterId, tenant);
        if (rows.isEmpty()) {
            throw BizException.notFound("表计不存在");
        }
        BigDecimal previous = (BigDecimal) rows.get(0).get("currentReading");
        if (cmd.readingValue().compareTo(previous) < 0) {
            throw BizException.param("本次读数不能小于上次读数");
        }
        BigDecimal usage = cmd.readingValue().subtract(previous);
        long id = idGen.nextId();
        LocalDate date = cmd.readingDate() == null ? LocalDate.now() : cmd.readingDate();
        jdbc.update("insert into guarantee_meter_reading(id,tenant_id,meter_id,reading_date,reading_value,"
                        + "previous_value,usage_amount,reader_name) values(?,?,?,?,?,?,?,?)",
                id, tenant, meterId, date, cmd.readingValue(), previous, usage, cmd.readerName());
        jdbc.update("update guarantee_meter set current_reading=?, update_time=now() where id=?",
                cmd.readingValue(), meterId);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", id);
        out.put("meterId", meterId);
        out.put("previousValue", previous);
        out.put("readingValue", cmd.readingValue());
        out.put("usageAmount", usage);
        return out;
    }

    public List<Map<String, Object>> summary(long projectId) {
        return jdbc.queryForList(
                "select m.meter_type meterType, count(distinct m.id) meterCount, "
                        + "coalesce(sum(r.usage_amount),0) usageAmount "
                        + "from guarantee_meter m left join guarantee_meter_reading r on r.meter_id=m.id "
                        + "where m.tenant_id=? and m.project_id=? and m.is_deleted=0 "
                        + "group by m.meter_type order by m.meter_type",
                TenantContext.require(), projectId);
    }

    private long count(String sql, Object... args) {
        Long value = jdbc.queryForObject(sql, Long.class, args);
        return value == null ? 0 : value;
    }

    public record MeterCmd(Long projectId, Long houseId, String meterType, String meterNo,
                           BigDecimal initialReading, LocalDate installDate) {
    }

    public record ReadingCmd(LocalDate readingDate, BigDecimal readingValue, String readerName) {
    }
}
