package com.yundao.platform.service;

import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.id.IdGenerator;
import com.yundao.platform.common.tenant.TenantContext;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class GuaranteeSubsidyService {

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;
    private final GuaranteeContractService contractService;

    public GuaranteeSubsidyService(JdbcTemplate jdbc, IdGenerator idGen,
                                   GuaranteeContractService contractService) {
        this.jdbc = jdbc;
        this.idGen = idGen;
        this.contractService = contractService;
    }

    public List<Map<String, Object>> list(long contractId) {
        contractService.load(contractId);
        return jdbc.queryForList(
                "select id, contract_id contractId, subsidy_type subsidyType, subsidy_amount subsidyAmount, "
                        + "start_date startDate, end_date endDate, subsidy_status subsidyStatus, remark "
                        + "from guarantee_subsidy where tenant_id=? and contract_id=? and is_deleted=0 "
                        + "order by id desc",
                TenantContext.require(), contractId);
    }

    public Map<String, Object> create(long contractId, SubsidyCmd cmd) {
        GuaranteeContractService.Contract contract = contractService.load(contractId);
        if (!"ACTIVE".equals(contract.contractStatus())) {
            throw BizException.param("合同不是生效状态");
        }
        if (cmd.amount() == null || cmd.amount().signum() < 0) {
            throw BizException.param("补贴金额不能为负数");
        }
        if (cmd.startDate() == null || cmd.endDate() == null || cmd.endDate().isBefore(cmd.startDate())) {
            throw BizException.param("补贴起止日期不合法");
        }
        long id = idGen.nextId();
        jdbc.update("insert into guarantee_subsidy(id,tenant_id,project_id,contract_id,subsidy_type,"
                        + "subsidy_amount,start_date,end_date,subsidy_status,remark,is_deleted) "
                        + "values(?,?,?,?,?,?,?,?, 'ACTIVE',?,0)",
                id, TenantContext.require(), contract.projectId(), contractId,
                cmd.subsidyType() == null ? "RENT_SUBSIDY" : cmd.subsidyType(),
                cmd.amount(), cmd.startDate(), cmd.endDate(), cmd.remark());
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", id);
        out.put("contractId", contractId);
        out.put("subsidyAmount", cmd.amount());
        out.put("subsidyStatus", "ACTIVE");
        return out;
    }

    public BigDecimal discountFor(long contractId, LocalDate periodStart, LocalDate periodEnd) {
        BigDecimal value = jdbc.queryForObject(
                "select coalesce(sum(subsidy_amount),0) from guarantee_subsidy "
                        + "where tenant_id=? and contract_id=? and subsidy_status='ACTIVE' and is_deleted=0 "
                        + "and subsidy_type='RENT_SUBSIDY' "
                        + "and start_date<=? and end_date>=?",
                BigDecimal.class, TenantContext.require(), contractId, periodEnd, periodStart);
        return value == null ? BigDecimal.ZERO : value;
    }


    public Map<String, Object> update(long subsidyId, SubsidyCmd cmd) {
        if (cmd.amount() == null || cmd.amount().signum() < 0) throw BizException.param("补贴金额不能为负数");
        if (cmd.startDate() == null || cmd.endDate() == null || cmd.endDate().isBefore(cmd.startDate())) {
            throw BizException.param("补贴起止日期不合法");
        }
        String subsidyType = cmd.subsidyType();
        if (subsidyType == null || subsidyType.isBlank()) {
            subsidyType = jdbc.queryForObject(
                    "select subsidy_type from guarantee_subsidy where id=? and tenant_id=? and is_deleted=0",
                    String.class, subsidyId, TenantContext.require());
        }
        int updated = jdbc.update("update guarantee_subsidy set subsidy_type=?, subsidy_amount=?, start_date=?, "
                        + "end_date=?, remark=?, update_time=now() where id=? and tenant_id=? and is_deleted=0",
                subsidyType, cmd.amount(), cmd.startDate(), cmd.endDate(), cmd.remark(),
                subsidyId, TenantContext.require());
        if (updated == 0) throw BizException.notFound("补贴不存在");
        return Map.of("id", subsidyId, "subsidyAmount", cmd.amount());
    }

    public Map<String, Object> terminate(long subsidyId) {
        int updated = jdbc.update("update guarantee_subsidy set subsidy_status='TERMINATED', update_time=now() "
                + "where id=? and tenant_id=? and is_deleted=0", subsidyId, TenantContext.require());
        if (updated == 0) throw BizException.notFound("补贴不存在");
        return Map.of("id", subsidyId, "subsidyStatus", "TERMINATED");
    }

    public record SubsidyCmd(String subsidyType, BigDecimal amount, LocalDate startDate,
                             LocalDate endDate, String remark) {
    }
}
