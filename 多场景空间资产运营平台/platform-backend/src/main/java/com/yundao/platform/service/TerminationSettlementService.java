package com.yundao.platform.service;

import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.tenant.TenantContext;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class TerminationSettlementService {
    private final JdbcTemplate jdbc;
    private final GuaranteeContractService contracts;
    private final GuaranteeDepositService deposits;

    public TerminationSettlementService(JdbcTemplate jdbc, GuaranteeContractService contracts, GuaranteeDepositService deposits) {
        this.jdbc = jdbc;
        this.contracts = contracts;
        this.deposits = deposits;
    }

    public Map<String, Object> preview(long contractId) {
        GuaranteeContractService.Contract contract = contracts.load(contractId);
        if (!"ACTIVE".equals(contract.contractStatus())) throw BizException.conflict("只有生效合同可以退租结算");
        BigDecimal unpaid = jdbc.queryForObject(
                "select coalesce(sum(greatest(payable_amount - paid_amount, 0)),0) from bp_bill where tenant_id=? and contract_id=? and bill_status in ('UNPAID','PARTIAL') and is_deleted=0",
                BigDecimal.class, TenantContext.require(), contractId);
        Map<String, Object> deposit = deposits.get(contractId);
        BigDecimal paid = (BigDecimal) deposit.getOrDefault("paidAmount", BigDecimal.ZERO);
        BigDecimal refunded = (BigDecimal) deposit.getOrDefault("refundedAmount", BigDecimal.ZERO);
        BigDecimal refundable = paid.subtract(refunded);
        if (refundable.signum() < 0) refundable = BigDecimal.ZERO;
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("contractId", contractId);
        out.put("contractNo", contract.contractNo());
        out.put("unpaidAmount", unpaid == null ? BigDecimal.ZERO : unpaid);
        out.put("depositPaid", paid);
        out.put("depositRefunded", refunded);
        out.put("refundableAmount", refundable);
        out.put("depositId", deposit.get("id"));
        return out;
    }

    @Transactional
    public Map<String, Object> settle(long contractId, LocalDate date, String reason) {
        Map<String, Object> preview = preview(contractId);
        if (((BigDecimal) preview.get("unpaidAmount")).signum() > 0) {
            throw BizException.conflict("退租前请先结清欠费");
        }
        GuaranteeContractService.Contract contract = contracts.load(contractId);
        LocalDate end = date == null ? LocalDate.now() : date;
        jdbc.update("update guarantee_contract set contract_status='TERMINATED', end_date=?, update_time=now() where id=? and tenant_id=?",
                end, contractId, TenantContext.require());
        jdbc.update("update bp_house set house_status='VACANT', update_time=now() where id=? and tenant_id=? and is_deleted=0",
                contract.houseId(), TenantContext.require());
        jdbc.update("update guarantee_allocation set allocation_status='TERMINATED' where contract_id=? and allocation_status='CONTRACTED'",
                contractId);
        jdbc.update("update bp_grant_entitlement set grant_status='REVOKED', revoke_reason=?, update_time=now() where tenant_id=? and source_type='CONTRACT' and source_id=? and grant_status='ACTIVE'",
                reason == null ? "退租回收" : reason, TenantContext.require(), contractId);
        jdbc.update("update bp_grant_entitlement set grant_status='REVOKED', revoke_reason=?, update_time=now() where tenant_id=? and person_id=? and target_type='SPACE' and target_id=(select space_id from bp_house where id=?) and grant_status='ACTIVE'",
                reason == null ? "退租回收" : reason, TenantContext.require(), contract.personId(), contract.houseId());
        jdbc.update("update bp_grant_entitlement set grant_status='REVOKED', revoke_reason=?, update_time=now() where tenant_id=? and person_id=? and target_type='DEVICE' and target_id in (select id from bp_dev_device where space_id=(select space_id from bp_house where id=?) and is_deleted=0) and grant_status='ACTIVE'",
                reason == null ? "退租回收" : reason, TenantContext.require(), contract.personId(), contract.houseId());
        BigDecimal refundable = (BigDecimal) preview.get("refundableAmount");
        if (refundable.signum() > 0) {
            deposits.refund(((Number) preview.get("depositId")).longValue(),
                    new GuaranteeDepositService.RefundCmd(refundable, "system", reason == null ? "退租结算" : reason));
        }
        Map<String, Object> out = new LinkedHashMap<>(preview);
        out.put("contractStatus", "TERMINATED");
        out.put("houseStatus", "VACANT");
        out.put("settledAt", end);
        return out;
    }
}
