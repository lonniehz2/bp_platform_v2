package com.yundao.bp.fin.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.fin.dto.LateFeePolicyCmd;
import com.yundao.bp.fin.entity.FinBill;
import com.yundao.bp.fin.entity.LateFeePolicy;
import com.yundao.bp.fin.mapper.FinBillMapper;
import com.yundao.bp.fin.mapper.LateFeePolicyMapper;
import com.yundao.bp.iam.entity.IamTenant;
import com.yundao.bp.iam.mapper.IamTenantMapper;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** 滞纳金：日利率 + 宽限期 + 封顶，单利按日。 */
@Service
public class LateFeeService {

    private static final Logger log = LoggerFactory.getLogger(LateFeeService.class);
    private static final BigDecimal DEFAULT_RATE = new BigDecimal("0.000500");
    private static final int DEFAULT_GRACE = 5;
    private static final BigDecimal DEFAULT_CAP = new BigDecimal("0.2000");

    private final LateFeePolicyMapper policyMapper;
    private final FinBillMapper billMapper;
    private final IamTenantMapper tenantMapper;
    private final SnowflakeIdGenerator idGen;

    public LateFeeService(LateFeePolicyMapper policyMapper, FinBillMapper billMapper,
                          IamTenantMapper tenantMapper, SnowflakeIdGenerator idGen) {
        this.policyMapper = policyMapper;
        this.billMapper = billMapper;
        this.tenantMapper = tenantMapper;
        this.idGen = idGen;
    }

    public LateFeePolicy policy(Long orgId) {
        List<LateFeePolicy> list = policyMapper.selectList(new LambdaQueryWrapper<LateFeePolicy>()
                .eq(LateFeePolicy::getStatus, "ENABLED"));
        for (LateFeePolicy p : list) {
            if (p.getOrgId() != null && p.getOrgId().equals(orgId)) {
                return p;
            }
        }
        for (LateFeePolicy p : list) {
            if (p.getOrgId() == null) {
                return p;
            }
        }
        return null;
    }

    public LateFeePolicy savePolicy(LateFeePolicyCmd cmd) {
        LateFeePolicy p = policy(cmd.orgId());
        boolean create = p == null || !java.util.Objects.equals(p.getOrgId(), cmd.orgId());
        if (create) {
            p = new LateFeePolicy();
            p.setId(idGen.nextId());
            p.setTenantId(TenantContext.tenantId());
            p.setOrgId(cmd.orgId());
            p.setCreateTime(LocalDateTime.now());
        }
        p.setDailyRate(cmd.dailyRate() == null ? DEFAULT_RATE : cmd.dailyRate());
        p.setGraceDays(cmd.graceDays() == null ? DEFAULT_GRACE : cmd.graceDays());
        p.setCapRate(cmd.capRate() == null ? DEFAULT_CAP : cmd.capRate());
        p.setStatus("ENABLED");
        p.setUpdateTime(LocalDateTime.now());
        if (create) {
            policyMapper.insert(p);
        } else {
            policyMapper.updateById(p);
        }
        return p;
    }

    /** 每日 01:00 计提；也可手工触发。 */
    @Scheduled(cron = "0 0 1 * * ?")
    public int runDaily() {
        List<IamTenant> tenants = tenantMapper.selectList(
                new LambdaQueryWrapper<IamTenant>()
                        .eq(IamTenant::getStatus, "ENABLED")
                        .eq(IamTenant::getDeleted, 0));
        int total = 0;
        for (IamTenant t : tenants) {
            final int[] one = {0};
            TenantContext.runAs(t.getTenantCode(),
                    () -> one[0] = calculate(LocalDate.now(), null));
            total += one[0];
        }
        log.info("滞纳金定时任务：{} 个平台，{} 张账单", tenants.size(), total);
        return total;
    }

    public int calculate(LocalDate today, Long billId) {
        List<FinBill> bills = billMapper.selectList(new LambdaQueryWrapper<FinBill>()
                .in(FinBill::getBillStatus, List.of("UNPAID", "PARTIAL", "OVERDUE"))
                .eq(FinBill::getIsDeleted, 0)
                .isNotNull(FinBill::getDueDate)
                .eq(billId != null, FinBill::getId, billId));
        int n = 0;
        for (FinBill b : bills) {
            LateFeePolicy p = policy(b.getOrgId());
            BigDecimal rate = p == null ? DEFAULT_RATE : p.getDailyRate();
            int grace = p == null ? DEFAULT_GRACE : p.getGraceDays();
            BigDecimal capRate = p == null ? DEFAULT_CAP : p.getCapRate();
            long overdue = ChronoUnit.DAYS.between(b.getDueDate(), today) - grace;
            if (overdue <= 0) {
                continue;
            }
            BigDecimal base = nz(b.getBillAmount()).subtract(nz(b.getDiscountAmount()))
                    .subtract(nz(b.getPaidAmount())).subtract(nz(b.getWaivedAmount()));
            if (base.compareTo(BigDecimal.ZERO) <= 0) {
                continue;
            }
            BigDecimal late = base.multiply(rate).multiply(BigDecimal.valueOf(overdue))
                    .setScale(2, RoundingMode.HALF_UP);
            BigDecimal cap = base.multiply(capRate).setScale(2, RoundingMode.HALF_UP);
            if (late.compareTo(cap) > 0) {
                late = cap;
            }
            BigDecimal payable = base.add(late).setScale(2, RoundingMode.HALF_UP);
            b.setLateFee(late);
            b.setLateFeeDays((int) overdue);
            b.setLateFeeDetail("{\"days\":" + overdue + ",\"rate\":" + rate
                    + ",\"lateFee\":" + late + "}");
            b.setPayableAmount(payable);
            b.setOverdueDays((int) overdue);
            b.setBillStatus(payable.compareTo(BigDecimal.ZERO) <= 0 ? "PAID" : "OVERDUE");
            b.setUpdateTime(LocalDateTime.now());
            billMapper.updateById(b);
            n++;
        }
        log.info("滞纳金计提：{} 张账单", n);
        return n;
    }

    private static BigDecimal nz(BigDecimal v) {
        return v == null ? BigDecimal.ZERO : v;
    }
}
