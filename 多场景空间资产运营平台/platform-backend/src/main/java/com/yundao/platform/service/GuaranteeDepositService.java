package com.yundao.platform.service;

import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.id.IdGenerator;
import com.yundao.platform.common.tenant.TenantContext;
import java.math.BigDecimal;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class GuaranteeDepositService {

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;

    public GuaranteeDepositService(JdbcTemplate jdbc, IdGenerator idGen) {
        this.jdbc = jdbc;
        this.idGen = idGen;
    }

    public Map<String, Object> get(long contractId) {
        Deposit deposit = loadByContract(contractId);
        List<Map<String, Object>> txns = jdbc.queryForList(
                "select id, txn_type txnType, amount, operator_name operatorName, remark, txn_time txnTime "
                        + "from guarantee_deposit_txn where tenant_id=? and deposit_id=? order by id",
                TenantContext.require(), deposit.id());
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", deposit.id());
        out.put("contractId", deposit.contractId());
        out.put("personId", deposit.personId());
        out.put("amount", deposit.amount());
        out.put("paidAmount", deposit.paidAmount());
        out.put("refundedAmount", deposit.refundedAmount());
        out.put("depositStatus", deposit.status());
        out.put("transactions", txns);
        return out;
    }

    @Transactional
    public Map<String, Object> pay(long contractId, PayCmd cmd) {
        Deposit deposit = loadByContract(contractId);
        if (cmd.amount() == null || cmd.amount().signum() <= 0) {
            throw BizException.param("押金收款金额必须大于 0");
        }
        BigDecimal outstanding = deposit.amount().subtract(deposit.paidAmount());
        if (outstanding.signum() <= 0) {
            throw BizException.conflict("押金已收齐");
        }
        if (cmd.amount().compareTo(outstanding) > 0) {
            throw BizException.param("押金收款超过应收金额");
        }
        BigDecimal paid = deposit.paidAmount().add(cmd.amount());
        String status = paid.compareTo(deposit.amount()) >= 0 ? "HELD" : "PARTIAL";
        jdbc.update("update guarantee_deposit set paid_amount=?, deposit_status=?, update_time=now() "
                + "where id=?", paid, status, deposit.id());
        jdbc.update("insert into guarantee_deposit_txn(id,tenant_id,deposit_id,txn_type,amount,"
                        + "operator_name,remark) values(?,?,?, 'PAY',?,?,?)",
                idGen.nextId(), TenantContext.require(), deposit.id(), cmd.amount(),
                cmd.operatorName(), cmd.remark());
        return Map.of("depositId", deposit.id(), "paidAmount", paid, "depositStatus", status);
    }

    @Transactional
    public Map<String, Object> refund(long depositId, RefundCmd cmd) {
        Deposit deposit = load(depositId);
        if (cmd.amount() == null || cmd.amount().signum() <= 0) {
            throw BizException.param("退款金额必须大于 0");
        }
        BigDecimal refundable = deposit.paidAmount().subtract(deposit.refundedAmount());
        if (refundable.signum() <= 0) {
            throw BizException.conflict("押金没有可退金额");
        }
        if (cmd.amount().compareTo(refundable) > 0) {
            throw BizException.param("退款金额超过可退金额");
        }
        BigDecimal refunded = deposit.refundedAmount().add(cmd.amount());
        String status = refunded.compareTo(deposit.paidAmount()) >= 0 ? "REFUNDED" : "PARTIAL_REFUNDED";
        jdbc.update("update guarantee_deposit set refunded_amount=?, deposit_status=?, update_time=now() "
                + "where id=?", refunded, status, depositId);
        jdbc.update("insert into guarantee_deposit_txn(id,tenant_id,deposit_id,txn_type,amount,"
                        + "operator_name,remark) values(?,?,?, 'REFUND',?,?,?)",
                idGen.nextId(), TenantContext.require(), depositId, cmd.amount(),
                cmd.operatorName(), cmd.reason());
        return Map.of("depositId", depositId, "refundedAmount", refunded, "depositStatus", status);
    }

    private Deposit loadByContract(long contractId) {
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select id, contract_id contractId, person_id personId, amount, paid_amount paidAmount, "
                        + "refunded_amount refundedAmount, deposit_status depositStatus "
                        + "from guarantee_deposit where tenant_id=? and contract_id=? and is_deleted=0 for update",
                TenantContext.require(), contractId);
        if (rows.isEmpty()) {
            throw BizException.notFound("押金记录不存在");
        }
        return map(rows.get(0));
    }

    private Deposit load(long depositId) {
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select id, contract_id contractId, person_id personId, amount, paid_amount paidAmount, "
                        + "refunded_amount refundedAmount, deposit_status depositStatus "
                        + "from guarantee_deposit where id=? and tenant_id=? and is_deleted=0 for update",
                depositId, TenantContext.require());
        if (rows.isEmpty()) {
            throw BizException.notFound("押金记录不存在");
        }
        return map(rows.get(0));
    }

    private Deposit map(Map<String, Object> row) {
        return new Deposit(((Number) row.get("id")).longValue(),
                ((Number) row.get("contractId")).longValue(),
                ((Number) row.get("personId")).longValue(),
                (BigDecimal) row.get("amount"),
                (BigDecimal) row.get("paidAmount"),
                (BigDecimal) row.get("refundedAmount"),
                String.valueOf(row.get("depositStatus")));
    }

    private record Deposit(long id, long contractId, long personId, BigDecimal amount,
                           BigDecimal paidAmount, BigDecimal refundedAmount, String status) {
    }

    public record PayCmd(BigDecimal amount, String operatorName, String remark) {
    }

    public record RefundCmd(BigDecimal amount, String operatorName, String reason) {
    }
}
