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
public class GuaranteeContractService {

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;

    public GuaranteeContractService(JdbcTemplate jdbc, IdGenerator idGen) {
        this.jdbc = jdbc;
        this.idGen = idGen;
    }

    public List<Map<String, Object>> list(long projectId) {
        return jdbc.queryForList(
                "select c.id, c.contract_no contractNo, c.project_id projectId, c.house_id houseId, "
                        + "h.house_name houseName, c.person_id personId, p.person_name personName, "
                        + "c.start_date startDate, c.end_date endDate, c.rent_amount rentAmount, "
                        + "c.deposit_amount depositAmount, c.billing_cycle billingCycle, c.bill_day billDay, "
                        + "c.contract_status contractStatus, c.create_time createTime "
                        + "from guarantee_contract c "
                        + "left join bp_house h on h.id=c.house_id "
                        + "left join bp_person p on p.id=c.person_id "
                        + "where c.tenant_id=? and c.project_id=? and c.is_deleted=0 order by c.id desc",
                TenantContext.require(), projectId);
    }

    @org.springframework.transaction.annotation.Transactional
    public Map<String, Object> create(ContractCmd cmd) {
        String tenant = TenantContext.require();
        requireGuaranteeProject(cmd.projectId());
        if (cmd.contractNo() == null || cmd.contractNo().isBlank()
                || cmd.houseId() == null || cmd.personId() == null
                || cmd.startDate() == null || cmd.endDate() == null) {
            throw BizException.param("合同编号、房屋、人员、起止日期不能为空");
        }
        if (cmd.endDate().isBefore(cmd.startDate())) {
            throw BizException.param("合同结束日期不能早于开始日期");
        }
        if (count("select count(*) from bp_house where id=? and tenant_id=? and org_id=? and is_deleted=0",
                cmd.houseId(), tenant, cmd.projectId()) == 0) {
            throw BizException.param("房屋不属于当前项目");
        }
        if (count("select count(*) from bp_person where id=? and tenant_id=? and is_deleted=0",
                cmd.personId(), tenant) == 0) {
            throw BizException.param("人员不存在");
        }
        long overlap = count("select count(*) from guarantee_contract where tenant_id=? and house_id=? "
                        + "and contract_status='ACTIVE' and is_deleted=0 "
                        + "and start_date<=? and end_date>=?",
                tenant, cmd.houseId(), cmd.endDate(), cmd.startDate());
        if (overlap > 0) {
            throw BizException.conflict("该房屋在合同期间已有生效合同");
        }
        long id = idGen.nextId();
        String initialStatus = Boolean.TRUE.equals(cmd.draft()) ? "DRAFT" : "ACTIVE";
        BigDecimal rent = cmd.rentAmount() == null ? BigDecimal.ZERO : cmd.rentAmount();
        BigDecimal deposit = cmd.depositAmount() == null ? BigDecimal.ZERO : cmd.depositAmount();
        if (rent.signum() < 0 || deposit.signum() < 0) {
            throw BizException.param("租金和押金不能为负数");
        }
        try {
            jdbc.update("insert into guarantee_contract(id,tenant_id,project_id,contract_no,house_id,person_id,"
                            + "start_date,end_date,rent_amount,deposit_amount,billing_cycle,bill_day,"
                            + "contract_status,is_deleted) values(?,?,?,?,?,?,?,?,?,?,?,?,?,0)",
                    id, tenant, cmd.projectId(), cmd.contractNo().trim(), cmd.houseId(), cmd.personId(),
                    cmd.startDate(), cmd.endDate(), rent, deposit,
                    cmd.billingCycle() == null ? "MONTH" : cmd.billingCycle(),
                    cmd.billDay() == null ? 1 : cmd.billDay(), initialStatus);
        } catch (DataIntegrityViolationException e) {
            throw BizException.conflict("合同编号已存在");
        }
        long depositId = idGen.nextId();
        jdbc.update("insert into guarantee_deposit(id,tenant_id,project_id,contract_id,person_id,amount,"
                        + "paid_amount,refunded_amount,deposit_status,is_deleted) "
                        + "values(?,?,?,?,?,?,0,0,?,0)",
                depositId, tenant, cmd.projectId(), id, cmd.personId(), deposit,
                deposit.signum() > 0 ? "PENDING" : "HELD");
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", id);
        out.put("contractNo", cmd.contractNo());
        out.put("projectId", cmd.projectId());
        out.put("houseId", cmd.houseId());
        out.put("personId", cmd.personId());
        out.put("rentAmount", rent);
        out.put("depositId", depositId);
        out.put("contractStatus", initialStatus);
        return out;
    }

    public Map<String, Object> submit(long contractId) {
        Contract contract = load(contractId);
        if (!"DRAFT".equals(contract.contractStatus())) {
            throw BizException.conflict("只有草稿合同可以提交");
        }
        jdbc.update("update guarantee_contract set contract_status='APPROVING', update_time=now() "
                + "where id=? and tenant_id=?", contractId, TenantContext.require());
        return Map.of("id", contractId, "contractStatus", "APPROVING");
    }

    public Map<String, Object> approve(long contractId) {
        Contract contract = load(contractId);
        if (!"APPROVING".equals(contract.contractStatus())) {
            throw BizException.conflict("只有审批中的合同可以通过");
        }
        long overlap = count("select count(*) from guarantee_contract where tenant_id=? and house_id=? "
                        + "and contract_status='ACTIVE' and is_deleted=0 and id<>? "
                        + "and start_date<=? and end_date>=?",
                TenantContext.require(), contract.houseId(), contractId, contract.endDate(), contract.startDate());
        if (overlap > 0) {
            throw BizException.conflict("该房屋在合同期间已有生效合同");
        }
        jdbc.update("update guarantee_contract set contract_status='ACTIVE', update_time=now() "
                + "where id=? and tenant_id=?", contractId, TenantContext.require());
        return Map.of("id", contractId, "contractStatus", "ACTIVE");
    }

    public Map<String, Object> activate(long contractId, String reason) {
        Contract contract = load(contractId);
        if (!"DRAFT".equals(contract.contractStatus())) {
            throw BizException.conflict("只有草稿合同可以直接生效");
        }
        long overlap = count("select count(*) from guarantee_contract where tenant_id=? and house_id=? "
                        + "and contract_status='ACTIVE' and is_deleted=0 and id<>? "
                        + "and start_date<=? and end_date>=?",
                TenantContext.require(), contract.houseId(), contractId, contract.endDate(), contract.startDate());
        if (overlap > 0) {
            throw BizException.conflict("该房屋在合同期间已有生效合同");
        }
        jdbc.update("update guarantee_contract set contract_status='ACTIVE', update_time=now() "
                + "where id=? and tenant_id=?", contractId, TenantContext.require());
        return Map.of("id", contractId, "contractStatus", "ACTIVE",
                "reason", reason == null ? "" : reason);
    }

    public Map<String, Object> withdraw(long contractId) {
        Contract contract = load(contractId);
        if (!"APPROVING".equals(contract.contractStatus())) {
            throw BizException.conflict("只有审批中的合同可以撤回");
        }
        jdbc.update("update guarantee_contract set contract_status='DRAFT', update_time=now() "
                + "where id=? and tenant_id=?", contractId, TenantContext.require());
        return Map.of("id", contractId, "contractStatus", "DRAFT");
    }

    public Map<String, Object> discard(long contractId) {
        Contract contract = load(contractId);
        if (!"DRAFT".equals(contract.contractStatus())) {
            throw BizException.conflict("只有草稿合同可以作废");
        }
        jdbc.update("update guarantee_contract set contract_status='DISCARDED', update_time=now() "
                + "where id=? and tenant_id=?", contractId, TenantContext.require());
        return Map.of("id", contractId, "contractStatus", "DISCARDED");
    }

    @org.springframework.transaction.annotation.Transactional
    public Map<String, Object> createFromAllocation(long allocationId, AllocationContractCmd cmd) {
        String tenant = TenantContext.require();
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select al.id, al.project_id projectId, al.house_id houseId, "
                        + "al.allocation_status allocationStatus, a.applicant_person_id personId "
                        + "from guarantee_allocation al join guarantee_application a on a.id=al.application_id "
                        + "where al.id=? and al.tenant_id=? and al.is_deleted=0 for update",
                allocationId, tenant);
        if (rows.isEmpty()) {
            throw BizException.notFound("配租记录不存在");
        }
        Map<String, Object> row = rows.get(0);
        if (!"ALLOCATED".equals(String.valueOf(row.get("allocationStatus")))) {
            throw BizException.conflict("配租记录不是待签约状态");
        }
        long projectId = ((Number) row.get("projectId")).longValue();
        long houseId = ((Number) row.get("houseId")).longValue();
        long personId = ((Number) row.get("personId")).longValue();
        Map<String, Object> contract = create(new ContractCmd(projectId, cmd.contractNo(), houseId, personId,
                cmd.startDate(), cmd.endDate(), cmd.rentAmount(), cmd.depositAmount(),
                cmd.billingCycle(), cmd.billDay(), false));
        long contractId = ((Number) contract.get("id")).longValue();
        jdbc.update("update guarantee_allocation set allocation_status='CONTRACTED', contract_id=? "
                + "where id=?", contractId, allocationId);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("allocationId", allocationId);
        out.put("contractId", contractId);
        out.put("allocationStatus", "CONTRACTED");
        return out;
    }

    public Contract load(long contractId) {
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select id, tenant_id tenantId, project_id projectId, contract_no contractNo, "
                        + "house_id houseId, person_id personId, rent_amount rentAmount, "
                        + "start_date startDate, end_date endDate, contract_status contractStatus "
                        + "from guarantee_contract where id=? and tenant_id=? and is_deleted=0",
                contractId, TenantContext.require());
        if (rows.isEmpty()) {
            throw BizException.notFound("保障房合同不存在");
        }
        Map<String, Object> r = rows.get(0);
        return new Contract(((Number) r.get("id")).longValue(),
                String.valueOf(r.get("tenantId")),
                ((Number) r.get("projectId")).longValue(),
                String.valueOf(r.get("contractNo")),
                ((Number) r.get("houseId")).longValue(),
                ((Number) r.get("personId")).longValue(),
                (BigDecimal) r.get("rentAmount"),
                (java.sql.Date) r.get("startDate"),
                (java.sql.Date) r.get("endDate"),
                String.valueOf(r.get("contractStatus")));
    }

    private void requireGuaranteeProject(long projectId) {
        if (count("select count(*) from bp_org where id=? and tenant_id=? and scene_code='GUARANTEE' "
                + "and is_deleted=0", projectId, TenantContext.require()) == 0) {
            throw BizException.param("项目不是保障房项目");
        }
    }

    private long count(String sql, Object... args) {
        Long value = jdbc.queryForObject(sql, Long.class, args);
        return value == null ? 0 : value;
    }

    public record ContractCmd(Long projectId, String contractNo, Long houseId, Long personId,
                              LocalDate startDate, LocalDate endDate, BigDecimal rentAmount,
                              BigDecimal depositAmount, String billingCycle, Integer billDay,
                              Boolean draft) {
    }

    public record AllocationContractCmd(String contractNo, LocalDate startDate, LocalDate endDate,
                                        BigDecimal rentAmount, BigDecimal depositAmount,
                                        String billingCycle, Integer billDay) {
    }

    public record Contract(long id, String tenantId, long projectId, String contractNo, long houseId,
                           long personId, BigDecimal rentAmount, java.sql.Date startDate,
                           java.sql.Date endDate, String contractStatus) {
    }
}
