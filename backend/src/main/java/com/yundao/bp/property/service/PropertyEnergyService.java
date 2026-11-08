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

/** 公共能耗按建筑面积分摊。 */
@Service
public class PropertyEnergyService {

    private final JdbcTemplate jdbc;
    private final SnowflakeIdGenerator idGen;

    public PropertyEnergyService(JdbcTemplate jdbc, SnowflakeIdGenerator idGen) {
        this.jdbc = jdbc;
        this.idGen = idGen;
    }

    public List<Map<String, Object>> list(Long projectId, String period) {
        requireProject(projectId);
        return jdbc.queryForList(
                "select a.id, a.period, a.house_id houseId, h.house_name houseName, a.area, "
                        + "a.total_amount totalAmount, a.total_area totalArea, a.amount, a.bill_id billId, "
                        + "a.status from prop_energy_allocation a "
                        + "left join bp_asset_house h on h.id=a.house_id "
                        + "where a.tenant_id=? and a.project_id=? and (? is null or a.period=?) "
                        + "order by a.id desc limit 300",
                TenantContext.tenantId(), projectId, period, period);
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> allocate(Long projectId, String period, BigDecimal totalAmount,
                                        Long feeItemId) {
        requireProject(projectId);
        if (period == null || !period.matches("\\d{4}-\\d{2}")) {
            throw BizException.paramInvalid("期间格式应为 yyyy-MM");
        }
        if (totalAmount == null || totalAmount.compareTo(BigDecimal.ZERO) <= 0) {
            throw BizException.paramInvalid("公摊总额必须大于 0");
        }
        Map<String, Object> fee = jdbc.queryForMap(
                "select id, income_category, income_subcategory from prop_fee_item "
                        + "where id=? and tenant_id=? and project_id=? and is_deleted=0",
                feeItemId, TenantContext.tenantId(), projectId);
        List<Map<String, Object>> houses = jdbc.queryForList(
                "select h.id, h.house_name houseName, h.area, "
                        + "coalesce((select ou.person_id from prop_owner_unit ou where ou.house_id=h.id "
                        + "and ou.is_primary=1 and ou.status='ACTIVE' and ou.is_deleted=0 limit 1), "
                        + "h.owner_person_id) ownerPersonId "
                        + "from bp_asset_house h join bp_asset_space s on s.id=h.space_id "
                        + "where h.tenant_id=? and h.org_id=? and h.is_deleted=0 "
                        + "and s.space_type='ROOM' and h.area is not null and h.area>0 order by h.house_code",
                TenantContext.tenantId(), projectId);
        if (houses.isEmpty()) throw BizException.stateConflict("项目没有可分摊的房屋");
        BigDecimal totalArea = houses.stream().map(h -> (BigDecimal) h.get("area"))
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        LocalDate start = YearMonth.parse(period).atDay(1);
        LocalDate end = YearMonth.parse(period).atEndOfMonth();
        int created = 0, skipped = 0;
        BigDecimal allocated = BigDecimal.ZERO;
        for (int i = 0; i < houses.size(); i++) {
            Map<String, Object> h = houses.get(i);
            Long houseId = ((Number) h.get("id")).longValue();
            Long exists = jdbc.queryForObject(
                    "select count(*) from prop_energy_allocation where tenant_id=? and project_id=? "
                            + "and period=? and house_id=?",
                    Long.class, TenantContext.tenantId(), projectId, period, houseId);
            if (exists != null && exists > 0) {
                skipped++;
                continue;
            }
            BigDecimal area = (BigDecimal) h.get("area");
            BigDecimal amount;
            if (i == houses.size() - 1) {
                amount = totalAmount.subtract(allocated);
            } else {
                amount = totalAmount.multiply(area).divide(totalArea, 2, RoundingMode.HALF_UP);
                allocated = allocated.add(amount);
            }
            long allocId = idGen.nextId();
            long billId = idGen.nextId();
            String billNo = "PB" + billId;
            Long owner = h.get("ownerPersonId") == null ? null : ((Number) h.get("ownerPersonId")).longValue();
            jdbc.update("insert into prop_energy_allocation(id,tenant_id,project_id,period,house_id,area,"
                            + "total_amount,total_area,amount,bill_id,status,create_time) "
                            + "values(?,?,?,?,?,?,?,?,?,?, 'BILLED',now())",
                    allocId, TenantContext.tenantId(), projectId, period, houseId, area,
                    totalAmount, totalArea, amount, billId);
            jdbc.update("insert into prop_bill(id,tenant_id,project_id,bill_no,income_category,"
                            + "income_subcategory,fee_item_id,payer_type,payer_person_id,payer_name,house_id,"
                            + "period_start,period_end,billing_cycle,cycle_count,quantity,unit_price,"
                            + "bill_amount,payable_amount,bill_status,due_date,source_type,source_id,"
                            + "service_start_date,service_end_date,is_deleted,create_by,create_time,"
                            + "update_by,update_time) values(?,?,?,?,?,?,?,?,?,?,?,?,?, 'MONTH',1,?,?,?,?, "
                            + "'PENDING',?, 'ENERGY_ALLOC',?,?,?,0,?,now(),?,now())",
                    billId, TenantContext.tenantId(), projectId, billNo,
                    fee.get("income_category"), fee.get("income_subcategory"), fee.get("id"),
                    owner == null ? "HOUSE" : "OWNER", owner, h.get("houseName"), houseId,
                    Date.valueOf(start), Date.valueOf(end), area, totalAmount, amount, amount,
                    Date.valueOf(end), allocId, Date.valueOf(start), Date.valueOf(end),
                    String.valueOf(TenantContext.userId()), String.valueOf(TenantContext.userId()));
            created++;
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("period", period);
        out.put("created", created);
        out.put("skipped", skipped);
        out.put("totalArea", totalArea);
        out.put("totalAmount", totalAmount);
        return out;
    }

    private void requireProject(Long projectId) {
        if (projectId == null) throw BizException.paramInvalid("请选择项目");
        Long n = jdbc.queryForObject("select count(*) from prop_project_config "
                        + "where tenant_id=? and org_id=? and is_deleted=0",
                Long.class, TenantContext.tenantId(), projectId);
        if (n == null || n == 0) throw BizException.notFound("物业项目");
    }
}
