package com.yundao.bp.property.service;

import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import java.math.BigDecimal;
import java.sql.Date;
import java.time.LocalDate;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** 物业租赁合同与租金账单。 */
@Service
public class PropertyLeaseService {

    private final JdbcTemplate jdbc;
    private final SnowflakeIdGenerator idGen;

    public PropertyLeaseService(JdbcTemplate jdbc, SnowflakeIdGenerator idGen) {
        this.jdbc = jdbc;
        this.idGen = idGen;
    }

    public List<Map<String, Object>> list(Long projectId) {
        requireProject(projectId);
        return jdbc.queryForList(
                "select id, contract_no contractNo, asset_type assetType, asset_name assetName, "
                        + "lessee_name lesseeName, lessee_phone lesseePhone, start_date startDate, "
                        + "end_date endDate, rent_amount rentAmount, billing_cycle billingCycle, "
                        + "next_bill_date nextBillDate, status from prop_lease_contract "
                        + "where tenant_id=? and project_id=? and is_deleted=0 order by id desc",
                TenantContext.tenantId(), projectId);
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> create(Long projectId, LeaseCmd cmd) {
        requireProject(projectId);
        if (cmd.assetName() == null || cmd.assetName().isBlank()
                || cmd.lesseeName() == null || cmd.lesseeName().isBlank()) {
            throw BizException.paramInvalid("租赁标的和承租方不能为空");
        }
        if (cmd.rentAmount() == null || cmd.rentAmount().compareTo(BigDecimal.ZERO) <= 0) {
            throw BizException.paramInvalid("租金必须大于 0");
        }
        if (cmd.startDate() == null || cmd.endDate() == null
                || cmd.endDate().isBefore(cmd.startDate())) {
            throw BizException.paramInvalid("合同起止日期不合法");
        }
        long id = idGen.nextId();
        String contractNo = "HT" + id;
        jdbc.update("insert into prop_lease_contract(id,tenant_id,project_id,contract_no,asset_type,"
                        + "asset_name,lessee_name,lessee_phone,start_date,end_date,rent_amount,"
                        + "billing_cycle,next_bill_date,status,remark,is_deleted,create_by,create_time,"
                        + "update_by,update_time) values(?,?,?,?,?,?,?,?,?,?,?,?,?, 'ACTIVE',?,0,?,now(),?,now())",
                id, TenantContext.tenantId(), projectId, contractNo,
                cmd.assetType() == null ? "SHOP" : cmd.assetType(), cmd.assetName().trim(),
                cmd.lesseeName().trim(), cmd.lesseePhone(), Date.valueOf(cmd.startDate()),
                Date.valueOf(cmd.endDate()), cmd.rentAmount(),
                cmd.billingCycle() == null ? "MONTH" : cmd.billingCycle(),
                Date.valueOf(cmd.startDate()), cmd.remark(),
                String.valueOf(TenantContext.userId()), String.valueOf(TenantContext.userId()));
        return Map.of("id", id, "contractNo", contractNo);
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> generate(Long projectId, Long contractId,
                                        LocalDate periodStart, LocalDate periodEnd) {
        requireProject(projectId);
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select * from prop_lease_contract where id=? and tenant_id=? and project_id=? "
                        + "and status='ACTIVE' and is_deleted=0",
                contractId, TenantContext.tenantId(), projectId);
        if (rows.isEmpty()) throw BizException.notFound("生效中的租赁合同");
        Map<String, Object> c = rows.get(0);
        Date nextBillDate = (Date) c.get("next_bill_date");
        LocalDate start = periodStart != null ? periodStart
                : (nextBillDate != null ? nextBillDate.toLocalDate()
                : ((Date) c.get("start_date")).toLocalDate());
        LocalDate end = periodEnd == null ? start.plusMonths(1).minusDays(1) : periodEnd;
        Long exists = jdbc.queryForObject("select count(*) from prop_bill where tenant_id=? and project_id=? "
                        + "and source_type='LEASE_CONTRACT' and source_id=? and period_start=? and period_end=? "
                        + "and is_deleted=0",
                Long.class, TenantContext.tenantId(), projectId, contractId,
                Date.valueOf(start), Date.valueOf(end));
        if (exists != null && exists > 0) throw BizException.stateConflict("该合同本期租金已生成");
        Map<String, Object> fee = jdbc.queryForMap(
                "select id, income_category, income_subcategory from prop_fee_item "
                        + "where tenant_id=? and project_id=? and fee_item_code='LEASE_RENT' and is_deleted=0",
                TenantContext.tenantId(), projectId);
        long billId = idGen.nextId();
        String billNo = "PB" + billId;
        BigDecimal amount = (BigDecimal) c.get("rent_amount");
        jdbc.update("insert into prop_bill(id,tenant_id,project_id,bill_no,income_category,income_subcategory,"
                        + "fee_item_id,payer_type,payer_name,contract_id,period_start,period_end,billing_cycle,"
                        + "cycle_count,bill_amount,payable_amount,bill_status,due_date,source_type,source_id,"
                        + "service_start_date,service_end_date,is_deleted,create_by,create_time,update_by,update_time) "
                        + "values(?,?,?,?,?,?,?, 'OTHER',?,?,?,?,?,1,?,?, 'PENDING',?, 'LEASE_CONTRACT',?,?,?,0,?,now(),?,now())",
                billId, TenantContext.tenantId(), projectId, billNo,
                fee.get("income_category"), fee.get("income_subcategory"), fee.get("id"),
                c.get("lessee_name"), contractId, Date.valueOf(start), Date.valueOf(end),
                c.get("billing_cycle"), amount, amount, Date.valueOf(end), contractId,
                Date.valueOf(start), Date.valueOf(end),
                String.valueOf(TenantContext.userId()), String.valueOf(TenantContext.userId()));
        jdbc.update("update prop_lease_contract set next_bill_date=?, update_time=now() where id=?",
                Date.valueOf(end.plusDays(1)), contractId);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("contractId", contractId);
        out.put("billId", billId);
        out.put("amount", amount);
        return out;
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> end(Long projectId, Long contractId) {
        requireProject(projectId);
        int n = jdbc.update("update prop_lease_contract set status='ENDED', update_time=now() "
                        + "where id=? and tenant_id=? and project_id=? and status='ACTIVE'",
                contractId, TenantContext.tenantId(), projectId);
        if (n == 0) throw BizException.stateConflict("租赁合同已结束");
        return Map.of("ended", n);
    }

    private void requireProject(Long projectId) {
        if (projectId == null) throw BizException.paramInvalid("请选择项目");
        Long n = jdbc.queryForObject("select count(*) from prop_project_config "
                        + "where tenant_id=? and org_id=? and is_deleted=0",
                Long.class, TenantContext.tenantId(), projectId);
        if (n == null || n == 0) throw BizException.notFound("物业项目");
    }

    public record LeaseCmd(String assetType, String assetName, String lesseeName, String lesseePhone,
                           LocalDate startDate, LocalDate endDate, BigDecimal rentAmount,
                           String billingCycle, String remark) {
    }
}
