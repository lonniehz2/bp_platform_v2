package com.yundao.bp.fin.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.biz.entity.BizContract;
import com.yundao.bp.biz.mapper.BizContractMapper;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.fin.constant.BillStatus;
import com.yundao.bp.fin.dto.PrepayPayInCmd;
import com.yundao.bp.fin.dto.PrepayRefundCmd;
import com.yundao.bp.fin.entity.FinBill;
import com.yundao.bp.fin.entity.FinPayment;
import com.yundao.bp.fin.entity.FinPaymentAllocate;
import com.yundao.bp.fin.entity.FinPrepayAccount;
import com.yundao.bp.fin.entity.FinPrepayFlow;
import com.yundao.bp.fin.mapper.FinBillMapper;
import com.yundao.bp.fin.mapper.FinPaymentAllocateMapper;
import com.yundao.bp.fin.mapper.FinPaymentMapper;
import com.yundao.bp.fin.mapper.FinPrepayAccountMapper;
import com.yundao.bp.fin.mapper.FinPrepayFlowMapper;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** 合同级预收余额。 */
@Service
public class PrepayService {

    private final FinPrepayAccountMapper accountMapper;
    private final FinPrepayFlowMapper flowMapper;
    private final FinBillMapper billMapper;
    private final FinPaymentMapper paymentMapper;
    private final FinPaymentAllocateMapper allocateMapper;
    private final BizContractMapper contractMapper;
    private final SnowflakeIdGenerator idGen;

    public PrepayService(FinPrepayAccountMapper accountMapper,
                         FinPrepayFlowMapper flowMapper,
                         FinBillMapper billMapper,
                         FinPaymentMapper paymentMapper,
                         FinPaymentAllocateMapper allocateMapper,
                         BizContractMapper contractMapper,
                         SnowflakeIdGenerator idGen) {
        this.accountMapper = accountMapper;
        this.flowMapper = flowMapper;
        this.billMapper = billMapper;
        this.paymentMapper = paymentMapper;
        this.allocateMapper = allocateMapper;
        this.contractMapper = contractMapper;
        this.idGen = idGen;
    }

    public Map<String, Object> account(Long contractId) {
        FinPrepayAccount a = find(contractId);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("contractId", contractId);
        out.put("balanceAmount", a == null ? zero() : a.getBalanceAmount());
        out.put("totalIn", a == null ? zero() : a.getTotalIn());
        out.put("totalOut", a == null ? zero() : a.getTotalOut());
        out.put("status", a == null ? "ACTIVE" : a.getStatus());
        List<Map<String, Object>> flows = flowMapper.selectList(
                        new LambdaQueryWrapper<FinPrepayFlow>()
                                .eq(FinPrepayFlow::getContractId, contractId)
                                .orderByDesc(FinPrepayFlow::getId))
                .stream().map(this::flowMap).toList();
        out.put("flows", flows);
        return out;
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> payIn(PrepayPayInCmd cmd) {
        if (cmd.amount() == null || cmd.amount().compareTo(BigDecimal.ZERO) <= 0) {
            throw BizException.paramInvalid("预收金额必须大于 0");
        }
        BizContract ct = contractMapper.selectById(cmd.contractId());
        if (ct == null) {
            throw BizException.notFound("合同");
        }
        FinPrepayAccount a = lockOrCreate(ct);
        BigDecimal amount = money(cmd.amount());
        a.setBalanceAmount(money(a.getBalanceAmount()).add(amount));
        a.setTotalIn(money(a.getTotalIn()).add(amount));
        a.setUpdateTime(LocalDateTime.now());
        accountMapper.updateById(a);

        FinPrepayFlow f = new FinPrepayFlow();
        f.setId(idGen.nextId());
        f.setTenantId(TenantContext.tenantId());
        f.setAccountId(a.getId());
        f.setContractId(cmd.contractId());
        f.setFlowType("IN");
        f.setAmount(amount);
        f.setBalanceAfter(a.getBalanceAmount());
        f.setBizType("PREPAY_IN");
        f.setPayChannel(cmd.payChannel());
        f.setTradeNo(cmd.tradeNo());
        f.setActualAmount(amount);
        f.setFeeAmount(zero());
        f.setRemark(cmd.remark());
        f.setCreateTime(LocalDateTime.now());
        flowMapper.insert(f);
        return account(cmd.contractId());
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> refund(PrepayRefundCmd cmd) {
        FinPrepayAccount a = lock(cmd.contractId());
        if (a == null) {
            throw BizException.notFound("预收账户");
        }
        BigDecimal amount = money(cmd.amount());
        BigDecimal fee = money(cmd.feeAmount());
        if (amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw BizException.paramInvalid("退款金额必须大于 0");
        }
        if (fee.compareTo(BigDecimal.ZERO) < 0 || fee.compareTo(amount) > 0) {
            throw BizException.paramInvalid("手续费不能为负且不能超过退款金额");
        }
        if (amount.compareTo(money(a.getBalanceAmount())) > 0) {
            throw BizException.paramInvalid("退款金额不能超过预收余额 " + a.getBalanceAmount());
        }
        a.setBalanceAmount(money(a.getBalanceAmount()).subtract(amount));
        a.setTotalOut(money(a.getTotalOut()).add(amount));
        a.setUpdateTime(LocalDateTime.now());
        accountMapper.updateById(a);

        FinPrepayFlow f = new FinPrepayFlow();
        f.setId(idGen.nextId());
        f.setTenantId(TenantContext.tenantId());
        f.setAccountId(a.getId());
        f.setContractId(cmd.contractId());
        f.setFlowType("REFUND");
        f.setAmount(amount);
        f.setBalanceAfter(a.getBalanceAmount());
        f.setBizType("PREPAY_REFUND");
        f.setPayChannel(cmd.payChannel());
        f.setTradeNo(cmd.tradeNo());
        f.setFeeAmount(fee);
        f.setActualAmount(amount.subtract(fee));
        f.setRemark(cmd.reason());
        f.setCreateTime(LocalDateTime.now());
        flowMapper.insert(f);
        return account(cmd.contractId());
    }

    /** 合同间预收结转（续租/换房）。 */
    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> transfer(Long fromContractId, Long toContractId, BigDecimal amount,
                                        String remark) {
        if (fromContractId == null || toContractId == null
                || fromContractId.equals(toContractId)) {
            throw BizException.paramInvalid("转出与转入合同不能相同");
        }
        BigDecimal amt = money(amount);
        if (amt.compareTo(BigDecimal.ZERO) <= 0) {
            throw BizException.paramInvalid("结转金额必须大于 0");
        }
        FinPrepayAccount from = lock(fromContractId);
        FinPrepayAccount to = lock(toContractId);
        if (from == null) {
            throw BizException.notFound("转出预收账户");
        }
        if (money(from.getBalanceAmount()).compareTo(amt) < 0) {
            throw BizException.paramInvalid("预收余额不足，当前余额 " + from.getBalanceAmount());
        }
        if (to == null) {
            BizContract ct = contractMapper.selectById(toContractId);
            if (ct == null) {
                throw BizException.notFound("转入合同");
            }
            to = createAccount(ct);
        }
        LocalDateTime now = LocalDateTime.now();
        from.setBalanceAmount(money(from.getBalanceAmount()).subtract(amt));
        from.setTotalOut(money(from.getTotalOut()).add(amt));
        from.setUpdateTime(now);
        accountMapper.updateById(from);
        to.setBalanceAmount(money(to.getBalanceAmount()).add(amt));
        to.setTotalIn(money(to.getTotalIn()).add(amt));
        to.setUpdateTime(now);
        accountMapper.updateById(to);

        writeFlow(from, "TRANSFER_OUT", amt, "PREPAY_TRANSFER", "结转至合同 " + toContractId + " " + (remark == null ? "" : remark), now);
        writeFlow(to, "TRANSFER_IN", amt, "PREPAY_TRANSFER", "合同 " + fromContractId + " 转入 " + (remark == null ? "" : remark), now);
        return account(fromContractId);
    }

    private void writeFlow(FinPrepayAccount a, String type, BigDecimal amount, String bizType,
                           String remark, LocalDateTime now) {
        FinPrepayFlow f = new FinPrepayFlow();
        f.setId(idGen.nextId());
        f.setTenantId(TenantContext.tenantId());
        f.setAccountId(a.getId());
        f.setContractId(a.getContractId());
        f.setFlowType(type);
        f.setAmount(amount);
        f.setBalanceAfter(a.getBalanceAmount());
        f.setBizType(bizType);
        f.setRemark(remark);
        f.setCreateTime(now);
        flowMapper.insert(f);
    }

    /** 补贴抵扣时账单已缴清，剩余补贴转入合同预收余额。 */
    @Transactional(rollbackFor = Exception.class)
    public void creditSubsidy(Long contractId, BigDecimal amount, String remark) {
        BigDecimal amt = money(amount);
        if (contractId == null || amt.compareTo(BigDecimal.ZERO) <= 0) {
            return;
        }
        BizContract ct = contractMapper.selectById(contractId);
        if (ct == null) {
            throw BizException.notFound("合同");
        }
        FinPrepayAccount a = lockOrCreate(ct);
        a.setBalanceAmount(money(a.getBalanceAmount()).add(amt));
        a.setTotalIn(money(a.getTotalIn()).add(amt));
        a.setUpdateTime(LocalDateTime.now());
        accountMapper.updateById(a);

        FinPrepayFlow f = new FinPrepayFlow();
        f.setId(idGen.nextId());
        f.setTenantId(TenantContext.tenantId());
        f.setAccountId(a.getId());
        f.setContractId(contractId);
        f.setFlowType("IN");
        f.setAmount(amt);
        f.setBalanceAfter(a.getBalanceAmount());
        f.setBizType("SUBSIDY_OFFSET");
        f.setRemark(remark);
        f.setActualAmount(amt);
        f.setFeeAmount(zero());
        f.setCreateTime(LocalDateTime.now());
        flowMapper.insert(f);
    }

    /** 账单生成后自动抵扣该合同预收余额。 */
    @Transactional(rollbackFor = Exception.class)
    public BigDecimal offsetBill(FinBill bill) {
        if (bill == null || bill.getContractId() == null || bill.getPayableAmount() == null) {
            return zero();
        }
        FinPrepayAccount a = lock(bill.getContractId());
        if (a == null || money(a.getBalanceAmount()).compareTo(BigDecimal.ZERO) <= 0) {
            return zero();
        }
        BigDecimal payable = money(bill.getPayableAmount());
        if (payable.compareTo(BigDecimal.ZERO) <= 0) {
            return zero();
        }
        BigDecimal use = money(a.getBalanceAmount()).min(payable);
        if (use.compareTo(BigDecimal.ZERO) <= 0) {
            return zero();
        }

        long payId = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();
        FinPayment p = new FinPayment();
        p.setId(payId);
        p.setTenantId(bill.getTenantId());
        p.setPaymentNo("PP" + payId);
        p.setOrgId(bill.getOrgId());
        p.setContractId(bill.getContractId());
        p.setPersonId(bill.getPersonId());
        p.setPayerName(bill.getPayerName());
        p.setPayAmount(use);
        p.setPayChannel("PREPAY");
        p.setPayTime(now);
        p.setPayStatus("SUCCESS");
        p.setReconcileStatus("RECONCILED");
        p.setReconciledAmount(use);
        p.setRemark("预收余额抵扣 " + bill.getBillNo());
        p.setCreateTime(now);
        paymentMapper.insert(p);

        FinPaymentAllocate al = new FinPaymentAllocate();
        al.setId(idGen.nextId());
        al.setTenantId(bill.getTenantId());
        al.setPaymentId(payId);
        al.setBillId(bill.getId());
        al.setAllocateAmount(use);
        al.setAllocateType("PAY");
        al.setCreateTime(now);
        allocateMapper.insert(al);

        bill.setPaidAmount(money(bill.getPaidAmount()).add(use));
        bill.setPayableAmount(payable.subtract(use));
        bill.setBillStatus(payable.subtract(use).compareTo(BigDecimal.ZERO) <= 0
                ? BillStatus.PAID.name() : BillStatus.PARTIAL.name());
        bill.setUpdateTime(now);
        billMapper.updateById(bill);

        a.setBalanceAmount(money(a.getBalanceAmount()).subtract(use));
        a.setTotalOut(money(a.getTotalOut()).add(use));
        a.setUpdateTime(now);
        accountMapper.updateById(a);

        FinPrepayFlow f = new FinPrepayFlow();
        f.setId(idGen.nextId());
        f.setTenantId(bill.getTenantId());
        f.setAccountId(a.getId());
        f.setContractId(bill.getContractId());
        f.setFlowType("OUT");
        f.setAmount(use);
        f.setBalanceAfter(a.getBalanceAmount());
        f.setBizType("BILL");
        f.setBizId(bill.getId());
        f.setRemark("预收抵扣账单 " + bill.getBillNo());
        f.setCreateTime(now);
        flowMapper.insert(f);
        return use;
    }

    /** 手工把余额抵扣到合同当前未缴账单。 */
    @Transactional(rollbackFor = Exception.class)
    public int applyToContract(Long contractId) {
        List<FinBill> bills = billMapper.selectList(new LambdaQueryWrapper<FinBill>()
                .eq(FinBill::getContractId, contractId)
                .eq(FinBill::getIsDeleted, 0)
                .in(FinBill::getBillStatus, List.of("UNPAID", "PARTIAL", "OVERDUE"))
                .orderByAsc(FinBill::getDueDate)
                .orderByAsc(FinBill::getId));
        int n = 0;
        for (FinBill b : bills) {
            if (offsetBill(b).compareTo(BigDecimal.ZERO) > 0) {
                n++;
            }
            FinPrepayAccount a = find(contractId);
            if (a == null || money(a.getBalanceAmount()).compareTo(BigDecimal.ZERO) <= 0) {
                break;
            }
        }
        return n;
    }

    private FinPrepayAccount find(Long contractId) {
        return accountMapper.selectOne(new LambdaQueryWrapper<FinPrepayAccount>()
                .eq(FinPrepayAccount::getContractId, contractId)
                .last("limit 1"));
    }

    private FinPrepayAccount lock(Long contractId) {
        return accountMapper.lockByContract(TenantContext.tenantId(), contractId);
    }

    private FinPrepayAccount createAccount(BizContract ct) {
        FinPrepayAccount a = new FinPrepayAccount();
        a.setId(idGen.nextId());
        a.setTenantId(TenantContext.tenantId());
        a.setContractId(ct.getId());
        a.setPersonId(ct.getLesseePersonId());
        a.setOrgId(ct.getOrgId());
        a.setBalanceAmount(zero());
        a.setTotalIn(zero());
        a.setTotalOut(zero());
        a.setStatus("ACTIVE");
        a.setCreateTime(LocalDateTime.now());
        a.setUpdateTime(LocalDateTime.now());
        accountMapper.insert(a);
        return a;
    }

    private FinPrepayAccount lockOrCreate(BizContract ct) {
        FinPrepayAccount a = lock(ct.getId());
        if (a != null) {
            return a;
        }
        return createAccount(ct);
    }

    private Map<String, Object> flowMap(FinPrepayFlow f) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", f.getId());
        m.put("flowType", f.getFlowType());
        m.put("amount", f.getAmount());
        m.put("balanceAfter", f.getBalanceAfter());
        m.put("bizType", f.getBizType());
        m.put("bizId", f.getBizId());
        m.put("payChannel", f.getPayChannel());
        m.put("feeAmount", f.getFeeAmount());
        m.put("actualAmount", f.getActualAmount());
        m.put("remark", f.getRemark());
        m.put("createTime", f.getCreateTime());
        return m;
    }

    private static BigDecimal money(BigDecimal v) {
        return (v == null ? BigDecimal.ZERO : v).setScale(2, RoundingMode.HALF_UP);
    }

    private static BigDecimal zero() {
        return BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP);
    }
}
