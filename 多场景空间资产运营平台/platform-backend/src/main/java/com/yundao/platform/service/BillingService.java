package com.yundao.platform.service;

import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.id.IdGenerator;
import com.yundao.platform.common.tenant.TenantContext;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class BillingService {

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;
    private final GuaranteeContractService contractService;
    private final GuaranteeSubsidyService subsidyService;

    public BillingService(JdbcTemplate jdbc, IdGenerator idGen,
                          GuaranteeContractService contractService,
                          GuaranteeSubsidyService subsidyService) {
        this.jdbc = jdbc;
        this.idGen = idGen;
        this.contractService = contractService;
        this.subsidyService = subsidyService;
    }

    public List<Map<String, Object>> bills(long projectId, String status) {
        return jdbc.queryForList(
                "select b.id, b.bill_no billNo, b.project_id projectId, b.biz_type bizType, "
                        + "b.contract_id contractId, b.house_id houseId, h.house_name houseName, "
                        + "b.person_id personId, p.person_name personName, b.fee_item_code feeItemCode, "
                        + "b.period_start periodStart, b.period_end periodEnd, b.amount, "
                        + "b.discount_amount discountAmount, b.payable_amount payableAmount, b.paid_amount paidAmount, "
                        + "b.bill_status billStatus, b.due_date dueDate, b.create_time createTime "
                        + "from bp_bill b left join bp_house h on h.id=b.house_id "
                        + "left join bp_person p on p.id=b.person_id "
                        + "where b.tenant_id=? and b.project_id=? and b.is_deleted=0 "
                        + "and (? is null or b.bill_status=?) order by b.id desc",
                TenantContext.require(), projectId, status, status);
    }

    public Map<String, Object> generate(long contractId, BillCmd cmd) {
        GuaranteeContractService.Contract contract = contractService.load(contractId);
        if (!"ACTIVE".equals(contract.contractStatus())) {
            throw BizException.param("合同不是生效状态");
        }
        if (cmd.periodStart() == null || cmd.periodEnd() == null) {
            throw BizException.param("账单周期不能为空");
        }
        if (cmd.periodEnd().isBefore(cmd.periodStart())) {
            throw BizException.param("账单结束日期不能早于开始日期");
        }
        BigDecimal gross = cmd.amount() == null ? contract.rentAmount() : cmd.amount();
        if (gross == null || gross.signum() <= 0) {
            throw BizException.param("账单金额必须大于 0");
        }
        BigDecimal discount = subsidyService.discountFor(contractId, cmd.periodStart(), cmd.periodEnd());
        if (discount.compareTo(gross) > 0) {
            discount = gross;
        }
        BigDecimal payable = gross.subtract(discount);
        long id = idGen.nextId();
        String billNo = "BL" + System.currentTimeMillis() + id % 1000;
        try {
            jdbc.update("insert into bp_bill(id,tenant_id,project_id,bill_no,biz_type,contract_type,"
                            + "contract_id,house_id,person_id,fee_item_code,period_start,period_end,amount,"
                            + "discount_amount,payable_amount,paid_amount,bill_status,due_date,source_type,source_id,is_deleted) "
                            + "values(?,?,?,?, 'GUARANTEE_RENT','GUARANTEE_CONTRACT',?,?,?,?,?,?,?,?,?,0,"
                            + "'UNPAID',?,'CONTRACT',?,0)",
                    id, contract.tenantId(), contract.projectId(), billNo, contract.id(),
                    contract.houseId(), contract.personId(), "GUARANTEE_RENT",
                    cmd.periodStart(), cmd.periodEnd(), gross, discount, payable,
                    cmd.dueDate() == null ? cmd.periodEnd() : cmd.dueDate(), contract.id());
        } catch (DataIntegrityViolationException e) {
            throw BizException.conflict("该合同同一周期已生成账单");
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", id);
        out.put("billNo", billNo);
        out.put("amount", gross);
        out.put("discountAmount", discount);
        out.put("payableAmount", payable);
        out.put("billStatus", "UNPAID");
        return out;
    }

    @Transactional
    public Map<String, Object> pay(long billId, PaymentCmd cmd) {
        String tenant = TenantContext.require();
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select id, project_id projectId, person_id personId, amount, payable_amount payableAmount, "
                        + "paid_amount paidAmount, bill_status billStatus from bp_bill "
                        + "where id=? and tenant_id=? and is_deleted=0 for update",
                billId, tenant);
        if (rows.isEmpty()) {
            throw BizException.notFound("账单不存在");
        }
        Map<String, Object> bill = rows.get(0);
        String status = String.valueOf(bill.get("billStatus"));
        if ("PAID".equals(status)) {
            throw BizException.conflict("账单已结清");
        }
        BigDecimal payable = (BigDecimal) bill.get("payableAmount");
        if (payable == null) {
            payable = (BigDecimal) bill.get("amount");
        }
        BigDecimal paid = (BigDecimal) bill.get("paidAmount");
        BigDecimal outstanding = payable.subtract(paid == null ? BigDecimal.ZERO : paid);
        BigDecimal payAmount = cmd.amount();
        if (payAmount == null || payAmount.signum() <= 0) {
            throw BizException.param("收款金额必须大于 0");
        }
        if (payAmount.compareTo(outstanding) > 0) {
            throw BizException.param("收款金额超过未收金额");
        }
        long paymentId = idGen.nextId();
        String paymentNo = "PAY" + System.currentTimeMillis() + paymentId % 1000;
        String receiptNo = "RCP" + System.currentTimeMillis() + paymentId % 1000;
        long projectId = ((Number) bill.get("projectId")).longValue();
        Long personId = bill.get("personId") == null ? null : ((Number) bill.get("personId")).longValue();
        jdbc.update("insert into bp_payment(id,tenant_id,project_id,payment_no,payer_person_id,amount,"
                        + "payment_method,payment_status,paid_time,is_deleted) "
                        + "values(?,?,?,?,?,?,?, 'SUCCESS', now(),0)",
                paymentId, tenant, projectId, paymentNo, personId, payAmount,
                cmd.paymentMethod() == null ? "CASH" : cmd.paymentMethod());
        long allocationId = idGen.nextId();
        jdbc.update("insert into bp_payment_allocation(id,tenant_id,payment_id,bill_id,amount) "
                + "values(?,?,?,?,?)", allocationId, tenant, paymentId, billId, payAmount);
        BigDecimal newPaid = (paid == null ? BigDecimal.ZERO : paid).add(payAmount);
        String newStatus = newPaid.compareTo(payable) >= 0 ? "PAID" : "PARTIAL";
        jdbc.update("update bp_bill set paid_amount=?, bill_status=?, update_time=now() where id=?",
                newPaid, newStatus, billId);
        long receiptId = idGen.nextId();
        jdbc.update("insert into bp_receipt(id,tenant_id,project_id,receipt_no,payment_id,amount,"
                        + "receipt_status,issued_time,is_deleted) values(?,?,?,?,?,?, 'ISSUED', now(),0)",
                receiptId, tenant, projectId, receiptNo, paymentId, payAmount);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("paymentId", paymentId);
        out.put("paymentNo", paymentNo);
        out.put("receiptId", receiptId);
        out.put("receiptNo", receiptNo);
        out.put("billStatus", newStatus);
        out.put("paidAmount", newPaid);
        return out;
    }



    public List<Map<String, Object>> contractBills(long contractId) {
        contractService.load(contractId);
        return jdbc.queryForList(
                "select b.id, b.bill_no billNo, b.contract_id contractId, b.house_id houseId, "
                        + "h.house_name houseName, b.period_start periodStart, b.period_end periodEnd, "
                        + "b.amount, b.discount_amount discountAmount, b.payable_amount payableAmount, "
                        + "b.paid_amount paidAmount, b.bill_status billStatus, b.due_date dueDate "
                        + "from bp_bill b left join bp_house h on h.id=b.house_id "
                        + "where b.tenant_id=? and b.contract_id=? and b.is_deleted=0 order by b.period_start, b.id",
                TenantContext.require(), contractId);
    }

    @Transactional
    public Map<String, Object> payContract(long contractId, ContractPayCmd cmd) {
        GuaranteeContractService.Contract contract = contractService.load(contractId);
        if (!"ACTIVE".equals(contract.contractStatus())) {
            throw BizException.conflict("合同不是生效状态，不能收款");
        }
        if (cmd.allocations() == null || cmd.allocations().isEmpty()) {
            throw BizException.param("请选择至少一笔账单");
        }
        Map<Long, BigDecimal> requested = new java.util.LinkedHashMap<>();
        for (Allocation a : cmd.allocations()) {
            if (a.billId() == null || a.amount() == null || a.amount().signum() <= 0) {
                throw BizException.param("每笔账单的收款金额必须大于 0");
            }
            if (requested.put(a.billId(), a.amount()) != null) {
                throw BizException.param("同一账单不能重复选择");
            }
        }
        String tenant = TenantContext.require();
        BigDecimal total = requested.values().stream().reduce(BigDecimal.ZERO, BigDecimal::add);
        long paymentId = idGen.nextId();
        String paymentNo = "PAY" + System.currentTimeMillis() + paymentId % 1000;
        String receiptNo = "RCP" + System.currentTimeMillis() + paymentId % 1000;
        jdbc.update("insert into bp_payment(id,tenant_id,project_id,payment_no,payer_person_id,amount,"
                        + "payment_method,payment_status,paid_time,is_deleted) "
                        + "values(?,?,?,?,?,?,?, 'SUCCESS', now(),0)",
                paymentId, tenant, contract.projectId(), paymentNo, contract.personId(), total,
                cmd.paymentMethod() == null ? "CASH" : cmd.paymentMethod());
        List<Map<String, Object>> allocated = new ArrayList<>();
        for (Map.Entry<Long, BigDecimal> entry : requested.entrySet()) {
            long billId = entry.getKey();
            BigDecimal amount = entry.getValue();
            List<Map<String, Object>> rows = jdbc.queryForList(
                    "select id, contract_id contractId, payable_amount payableAmount, paid_amount paidAmount, "
                            + "bill_status billStatus from bp_bill "
                            + "where id=? and tenant_id=? and is_deleted=0 for update",
                    billId, tenant);
            if (rows.isEmpty()) {
                throw BizException.notFound("账单不存在");
            }
            Map<String, Object> bill = rows.get(0);
            if (!String.valueOf(contractId).equals(String.valueOf(bill.get("contractId")))) {
                throw BizException.param("账单不属于当前合同");
            }
            if ("PAID".equals(String.valueOf(bill.get("billStatus")))) {
                throw BizException.conflict("账单已结清");
            }
            BigDecimal payable = (BigDecimal) bill.get("payableAmount");
            if (payable == null) payable = BigDecimal.ZERO;
            BigDecimal paid = (BigDecimal) bill.get("paidAmount");
            if (paid == null) paid = BigDecimal.ZERO;
            BigDecimal outstanding = payable.subtract(paid);
            if (amount.compareTo(outstanding) > 0) {
                throw BizException.param("收款金额超过账单未收金额");
            }
            jdbc.update("insert into bp_payment_allocation(id,tenant_id,payment_id,bill_id,amount) "
                    + "values(?,?,?,?,?)", idGen.nextId(), tenant, paymentId, billId, amount);
            BigDecimal newPaid = paid.add(amount);
            String newStatus = newPaid.compareTo(payable) >= 0 ? "PAID" : "PARTIAL";
            jdbc.update("update bp_bill set paid_amount=?, bill_status=?, update_time=now() where id=?",
                    newPaid, newStatus, billId);
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("billId", billId);
            item.put("amount", amount);
            item.put("paidAmount", newPaid);
            item.put("billStatus", newStatus);
            allocated.add(item);
        }
        long receiptId = idGen.nextId();
        jdbc.update("insert into bp_receipt(id,tenant_id,project_id,receipt_no,payment_id,amount,"
                        + "receipt_status,issued_time,is_deleted) values(?,?,?,?,?,?, 'ISSUED', now(),0)",
                receiptId, tenant, contract.projectId(), receiptNo, paymentId, total);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("paymentId", paymentId);
        out.put("paymentNo", paymentNo);
        out.put("receiptId", receiptId);
        out.put("receiptNo", receiptNo);
        out.put("totalAmount", total);
        out.put("allocations", allocated);
        return out;
    }

    @Transactional
    public Map<String, Object> adjust(long billId, AdjustCmd cmd) {
        String tenant = TenantContext.require();
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select id, amount, discount_amount discountAmount, paid_amount paidAmount, bill_status billStatus "
                        + "from bp_bill where id=? and tenant_id=? and is_deleted=0 for update",
                billId, tenant);
        if (rows.isEmpty()) {
            throw BizException.notFound("账单不存在");
        }
        Map<String, Object> bill = rows.get(0);
        if ("PAID".equals(String.valueOf(bill.get("billStatus")))) {
            throw BizException.conflict("已结清账单不能调整");
        }
        BigDecimal amount = (BigDecimal) bill.get("amount");
        BigDecimal oldDiscount = (BigDecimal) bill.get("discountAmount");
        BigDecimal add = cmd.discountAmount() == null ? BigDecimal.ZERO : cmd.discountAmount();
        if (add.signum() < 0) {
            throw BizException.param("调整金额不能为负数");
        }
        BigDecimal discount = (oldDiscount == null ? BigDecimal.ZERO : oldDiscount).add(add);
        if (discount.compareTo(amount) > 0) {
            discount = amount;
        }
        BigDecimal payable = amount.subtract(discount);
        BigDecimal paid = (BigDecimal) bill.get("paidAmount");
        if (paid == null) paid = BigDecimal.ZERO;
        String status = payable.signum() == 0 ? "WAIVED"
                : paid.compareTo(payable) >= 0 ? "PAID"
                : paid.signum() > 0 ? "PARTIAL" : "UNPAID";
        jdbc.update("update bp_bill set discount_amount=?, payable_amount=?, bill_status=?, "
                        + "remark=concat(coalesce(remark,''), ?), update_time=now() where id=?",
                discount, payable, status, "\n调整:" + (cmd.remark() == null ? "" : cmd.remark()), billId);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("billId", billId);
        out.put("discountAmount", discount);
        out.put("payableAmount", payable);
        out.put("billStatus", status);
        return out;
    }

    public List<Map<String, Object>> payments(long projectId) {
        return jdbc.queryForList(
                "select p.id, p.payment_no paymentNo, p.project_id projectId, p.payer_person_id payerPersonId, "
                        + "p.amount, p.payment_method paymentMethod, p.payment_status paymentStatus, "
                        + "p.paid_time paidTime, r.receipt_no receiptNo "
                        + "from bp_payment p left join bp_receipt r on r.payment_id=p.id "
                        + "where p.tenant_id=? and p.project_id=? and p.is_deleted=0 order by p.id desc",
                TenantContext.require(), projectId);
    }

    public Map<String, Object> receipt(long paymentId) {
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select r.id, r.receipt_no receiptNo, r.payment_id paymentId, r.amount, "
                        + "r.receipt_status receiptStatus, r.issued_time issuedTime, p.payment_no paymentNo "
                        + "from bp_receipt r join bp_payment p on p.id=r.payment_id "
                        + "where r.tenant_id=? and r.payment_id=? and r.is_deleted=0",
                TenantContext.require(), paymentId);
        if (rows.isEmpty()) {
            throw BizException.notFound("收据不存在");
        }
        return rows.get(0);
    }

    public record BillCmd(LocalDate periodStart, LocalDate periodEnd, BigDecimal amount, LocalDate dueDate) {
    }

    public record PaymentCmd(BigDecimal amount, String paymentMethod) {
    }

    public record AdjustCmd(BigDecimal discountAmount, String remark) {
    }

    public record Allocation(Long billId, BigDecimal amount) {
    }

    public record ContractPayCmd(String paymentMethod, String remark, List<Allocation> allocations) {
    }

    public record Receipt(String receiptNo, LocalDateTime issuedTime) {
    }
}
