package com.yundao.bp.fin.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.fin.constant.BillStatus;
import com.yundao.bp.fin.dto.DevicePrepayConsumeCmd;
import com.yundao.bp.fin.dto.DevicePrepayInCmd;
import com.yundao.bp.fin.dto.DevicePrepayRefundCmd;
import com.yundao.bp.fin.entity.FinBill;
import com.yundao.bp.fin.entity.FinDevicePrepayAccount;
import com.yundao.bp.fin.entity.FinDevicePrepayFlow;
import com.yundao.bp.fin.entity.FinPayment;
import com.yundao.bp.fin.entity.FinPaymentAllocate;
import com.yundao.bp.fin.entity.MeterPoint;
import com.yundao.bp.fin.mapper.FinBillMapper;
import com.yundao.bp.fin.mapper.FinDevicePrepayAccountMapper;
import com.yundao.bp.fin.mapper.FinDevicePrepayFlowMapper;
import com.yundao.bp.fin.mapper.FinPaymentAllocateMapper;
import com.yundao.bp.fin.mapper.FinPaymentMapper;
import com.yundao.bp.fin.mapper.MeterPointMapper;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** 设备/表计水电预存。 */
@Service
public class DevicePrepayService {

    private final FinDevicePrepayAccountMapper accountMapper;
    private final FinDevicePrepayFlowMapper flowMapper;
    private final MeterPointMapper pointMapper;
    private final FinBillMapper billMapper;
    private final FinPaymentMapper paymentMapper;
    private final FinPaymentAllocateMapper allocateMapper;
    private final SnowflakeIdGenerator idGen;

    public DevicePrepayService(FinDevicePrepayAccountMapper accountMapper,
                               FinDevicePrepayFlowMapper flowMapper,
                               MeterPointMapper pointMapper,
                               FinBillMapper billMapper,
                               FinPaymentMapper paymentMapper,
                               FinPaymentAllocateMapper allocateMapper,
                               SnowflakeIdGenerator idGen) {
        this.accountMapper = accountMapper;
        this.flowMapper = flowMapper;
        this.pointMapper = pointMapper;
        this.billMapper = billMapper;
        this.paymentMapper = paymentMapper;
        this.allocateMapper = allocateMapper;
        this.idGen = idGen;
    }

    public Map<String, Object> account(Long meterPointId) {
        MeterPoint p = pointMapper.selectById(meterPointId);
        if (p == null) {
            throw BizException.notFound("表计点位");
        }
        FinDevicePrepayAccount a = find(meterPointId);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("meterPointId", meterPointId);
        out.put("meterName", p.getMeterName());
        out.put("meterScope", p.getMeterScope());
        out.put("spaceId", p.getSpaceId());
        out.put("contractId", a == null ? null : a.getContractId());
        out.put("balanceAmount", a == null ? zero() : a.getBalanceAmount());
        out.put("totalIn", a == null ? zero() : a.getTotalIn());
        out.put("totalOut", a == null ? zero() : a.getTotalOut());
        out.put("status", a == null ? "ACTIVE" : a.getStatus());
        List<Map<String, Object>> flows = flowMapper.selectList(
                        new LambdaQueryWrapper<FinDevicePrepayFlow>()
                                .eq(FinDevicePrepayFlow::getMeterPointId, meterPointId)
                                .orderByDesc(FinDevicePrepayFlow::getId))
                .stream().map(this::flowMap).toList();
        out.put("flows", flows);
        return out;
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> payIn(DevicePrepayInCmd cmd) {
        MeterPoint p = pointMapper.selectById(cmd.meterPointId());
        if (p == null) {
            throw BizException.notFound("表计点位");
        }
        BigDecimal amount = money(cmd.amount());
        if (amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw BizException.paramInvalid("预存金额必须大于 0");
        }
        FinDevicePrepayAccount a = lockOrCreate(p, cmd.contractId());
        a.setBalanceAmount(money(a.getBalanceAmount()).add(amount));
        a.setTotalIn(money(a.getTotalIn()).add(amount));
        a.setUpdateTime(LocalDateTime.now());
        accountMapper.updateById(a);

        FinDevicePrepayFlow f = new FinDevicePrepayFlow();
        f.setId(idGen.nextId());
        f.setTenantId(TenantContext.tenantId());
        f.setAccountId(a.getId());
        f.setMeterPointId(cmd.meterPointId());
        f.setContractId(a.getContractId());
        f.setFlowType("IN");
        f.setAmount(amount);
        f.setBalanceAfter(a.getBalanceAmount());
        f.setBizType("DEVICE_PREPAY_IN");
        f.setActualAmount(amount);
        f.setFeeAmount(zero());
        f.setRemark(cmd.remark());
        f.setCreateTime(LocalDateTime.now());
        flowMapper.insert(f);
        return account(cmd.meterPointId());
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> consume(DevicePrepayConsumeCmd cmd) {
        FinDevicePrepayAccount a = lock(cmd.meterPointId());
        if (a == null) {
            throw BizException.notFound("设备预存账户");
        }
        BigDecimal amount = money(cmd.amount());
        if (amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw BizException.paramInvalid("扣减金额必须大于 0");
        }
        BigDecimal balance = money(a.getBalanceAmount());
        if (amount.compareTo(balance) > 0) {
            throw BizException.paramInvalid("预存余额不足，当前余额 " + balance);
        }
        consume(a, amount, cmd.usageAmount(), cmd.readingValue(), cmd.billId(), cmd.remark());
        return account(cmd.meterPointId());
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> refund(DevicePrepayRefundCmd cmd) {
        FinDevicePrepayAccount a = lock(cmd.meterPointId());
        if (a == null) {
            throw BizException.notFound("设备预存账户");
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
            throw BizException.paramInvalid("退款金额不能超过设备预存余额 " + a.getBalanceAmount());
        }
        a.setBalanceAmount(money(a.getBalanceAmount()).subtract(amount));
        a.setTotalOut(money(a.getTotalOut()).add(amount));
        a.setUpdateTime(LocalDateTime.now());
        accountMapper.updateById(a);

        FinDevicePrepayFlow f = new FinDevicePrepayFlow();
        f.setId(idGen.nextId());
        f.setTenantId(TenantContext.tenantId());
        f.setAccountId(a.getId());
        f.setMeterPointId(cmd.meterPointId());
        f.setContractId(a.getContractId());
        f.setFlowType("REFUND");
        f.setAmount(amount);
        f.setBalanceAfter(a.getBalanceAmount());
        f.setBizType("DEVICE_PREPAY_REFUND");
        f.setFeeAmount(fee);
        f.setActualAmount(amount.subtract(fee));
        f.setRemark(cmd.reason());
        f.setCreateTime(LocalDateTime.now());
        flowMapper.insert(f);
        return account(cmd.meterPointId());
    }

    /** 抄表/能耗账单生成后，用设备预存抵扣账单。 */
    @Transactional(rollbackFor = Exception.class)
    public BigDecimal applyToBill(Long billId, Long meterPointId) {
        FinBill bill = billMapper.selectById(billId);
        if (bill == null || bill.getPayableAmount() == null) {
            return zero();
        }
        FinDevicePrepayAccount a = lock(meterPointId);
        if (a == null || money(a.getBalanceAmount()).compareTo(BigDecimal.ZERO) <= 0) {
            return zero();
        }
        BigDecimal payable = money(bill.getPayableAmount());
        BigDecimal use = money(a.getBalanceAmount()).min(payable);
        if (use.compareTo(BigDecimal.ZERO) <= 0) {
            return zero();
        }

        long payId = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();
        FinPayment p = new FinPayment();
        p.setId(payId);
        p.setTenantId(bill.getTenantId());
        p.setPaymentNo("DP" + payId);
        p.setOrgId(bill.getOrgId());
        p.setContractId(bill.getContractId());
        p.setPersonId(bill.getPersonId());
        p.setPayerName(bill.getPayerName());
        p.setPayAmount(use);
        p.setPayChannel("DEVICE_PREPAY");
        p.setPayTime(now);
        p.setPayStatus("SUCCESS");
        p.setReconcileStatus("RECONCILED");
        p.setReconciledAmount(use);
        p.setRemark("设备预存抵扣 " + bill.getBillNo());
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

        consume(a, use, null, null, billId, "抵扣账单 " + bill.getBillNo());
        return use;
    }

    private void consume(FinDevicePrepayAccount a, BigDecimal amount, BigDecimal usage,
                         BigDecimal reading, Long billId, String remark) {
        a.setBalanceAmount(money(a.getBalanceAmount()).subtract(amount));
        a.setTotalOut(money(a.getTotalOut()).add(amount));
        a.setUpdateTime(LocalDateTime.now());
        accountMapper.updateById(a);

        FinDevicePrepayFlow f = new FinDevicePrepayFlow();
        f.setId(idGen.nextId());
        f.setTenantId(TenantContext.tenantId());
        f.setAccountId(a.getId());
        f.setMeterPointId(a.getMeterPointId());
        f.setContractId(a.getContractId());
        f.setFlowType("OUT");
        f.setAmount(amount);
        f.setBalanceAfter(a.getBalanceAmount());
        f.setReadingValue(reading);
        f.setUsageAmount(usage);
        f.setBizType(billId == null ? "DEVICE_CONSUME" : "BILL");
        f.setBizId(billId);
        f.setRemark(remark);
        f.setCreateTime(LocalDateTime.now());
        flowMapper.insert(f);
    }

    private FinDevicePrepayAccount find(Long pointId) {
        return accountMapper.selectOne(new LambdaQueryWrapper<FinDevicePrepayAccount>()
                .eq(FinDevicePrepayAccount::getMeterPointId, pointId)
                .last("limit 1"));
    }

    private FinDevicePrepayAccount lock(Long pointId) {
        return accountMapper.lockByPoint(TenantContext.tenantId(), pointId);
    }

    private FinDevicePrepayAccount lockOrCreate(MeterPoint p, Long contractId) {
        FinDevicePrepayAccount a = lock(p.getId());
        if (a != null) {
            if (a.getContractId() == null && contractId != null) {
                a.setContractId(contractId);
            }
            return a;
        }
        a = new FinDevicePrepayAccount();
        a.setId(idGen.nextId());
        a.setTenantId(TenantContext.tenantId());
        a.setMeterPointId(p.getId());
        a.setContractId(contractId);
        a.setSpaceId(p.getSpaceId());
        a.setBalanceAmount(zero());
        a.setTotalIn(zero());
        a.setTotalOut(zero());
        a.setStatus("ACTIVE");
        a.setCreateTime(LocalDateTime.now());
        a.setUpdateTime(LocalDateTime.now());
        accountMapper.insert(a);
        return a;
    }

    private Map<String, Object> flowMap(FinDevicePrepayFlow f) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", f.getId());
        m.put("flowType", f.getFlowType());
        m.put("amount", f.getAmount());
        m.put("balanceAfter", f.getBalanceAfter());
        m.put("readingValue", f.getReadingValue());
        m.put("usageAmount", f.getUsageAmount());
        m.put("bizType", f.getBizType());
        m.put("bizId", f.getBizId());
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
