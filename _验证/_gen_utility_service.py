# -*- coding: utf-8 -*-
import io
import os

BASE = r'..\backend\src\main\java\com\yundao\bp\fin'
files = {}

files['dto/MeterPointCmd.java'] = '''package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.NotNull;

public record MeterPointCmd(
        @NotNull(message = "空间不能为空") Long spaceId,
        @NotNull(message = "收费项目不能为空") Long feeItemId,
        String meterScope,
        String allocationBasis,
        String meterName,
        String status
) {
}
'''

files['dto/MeterReadCmd.java'] = '''package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.time.LocalDateTime;

public record MeterReadCmd(
        @NotNull(message = "读数不能为空") BigDecimal reading,
        LocalDateTime readTime,
        String source,
        String photoUrl,
        String remark
) {
}
'''

files['dto/UtilityShareVO.java'] = '''package com.yundao.bp.fin.dto;

import java.math.BigDecimal;

public record UtilityShareVO(
        Long contractId,
        String contractNo,
        String lesseeName,
        Integer occupyDays,
        BigDecimal personDays,
        BigDecimal shareRatio,
        BigDecimal shareAmount
) {
}
'''

files['dto/UtilityAllocationVO.java'] = '''package com.yundao.bp.fin.dto;

import java.math.BigDecimal;
import java.util.List;

public record UtilityAllocationVO(
        Long id,
        Long meterPointId,
        String meterName,
        String period,
        BigDecimal startReading,
        BigDecimal endReading,
        BigDecimal totalUsage,
        BigDecimal totalAmount,
        BigDecimal operatorBearAmount,
        List<UtilityShareVO> shares
) {
}
'''

files['dto/EnergyStatVO.java'] = '''package com.yundao.bp.fin.dto;

import java.math.BigDecimal;

public record EnergyStatVO(
        String period,
        BigDecimal totalUsage,
        BigDecimal submeterUsage,
        BigDecimal diffUsage,
        BigDecimal diffRate,
        String alertLevel
) {
}
'''

files['dto/EnergyPolicyCmd.java'] = '''package com.yundao.bp.fin.dto;

import java.math.BigDecimal;

public record EnergyPolicyCmd(
        Long orgId,
        String vacancyBearer,
        BigDecimal warnRate,
        BigDecimal alarmRate
) {
}
'''

files['service/UtilityAllocationService.java'] = '''package com.yundao.bp.fin.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.asset.entity.AssetHouse;
import com.yundao.bp.asset.mapper.AssetHouseMapper;
import com.yundao.bp.biz.constant.ContractStatus;
import com.yundao.bp.biz.entity.BizContract;
import com.yundao.bp.biz.entity.BizContractCohabitant;
import com.yundao.bp.biz.mapper.BizContractCohabitantMapper;
import com.yundao.bp.biz.mapper.BizContractMapper;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.fin.constant.CalcMode;
import com.yundao.bp.fin.dto.*;
import com.yundao.bp.fin.entity.*;
import com.yundao.bp.fin.mapper.*;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.YearMonth;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** 房间表能耗分摊：整表算一次费用，按人·天分摊，空床默认运营方承担。 */
@Service
public class UtilityAllocationService {

    private static final DateTimeFormatter PERIOD = DateTimeFormatter.ofPattern("yyyy-MM");

    private final MeterPointMapper pointMapper;
    private final UtilityAllocationMapper allocationMapper;
    private final UtilityShareMapper shareMapper;
    private final EnergyPolicyMapper policyMapper;
    private final EnergyMonthlyStatMapper statMapper;
    private final BizContractMapper contractMapper;
    private final BizContractCohabitantMapper cohabitantMapper;
    private final FinFeeItemMapper feeItemMapper;
    private final FinBillingRuleMapper ruleMapper;
    private final FinBillMapper billMapper;
    private final AssetHouseMapper houseMapper;
    private final BillingCalculator calculator;
    private final SnowflakeIdGenerator idGen;
    private final JdbcTemplate jdbc;

    public UtilityAllocationService(MeterPointMapper pointMapper,
                                    UtilityAllocationMapper allocationMapper,
                                    UtilityShareMapper shareMapper,
                                    EnergyPolicyMapper policyMapper,
                                    EnergyMonthlyStatMapper statMapper,
                                    BizContractMapper contractMapper,
                                    BizContractCohabitantMapper cohabitantMapper,
                                    FinFeeItemMapper feeItemMapper,
                                    FinBillingRuleMapper ruleMapper,
                                    FinBillMapper billMapper,
                                    AssetHouseMapper houseMapper,
                                    BillingCalculator calculator,
                                    SnowflakeIdGenerator idGen,
                                    JdbcTemplate jdbc) {
        this.pointMapper = pointMapper;
        this.allocationMapper = allocationMapper;
        this.shareMapper = shareMapper;
        this.policyMapper = policyMapper;
        this.statMapper = statMapper;
        this.contractMapper = contractMapper;
        this.cohabitantMapper = cohabitantMapper;
        this.feeItemMapper = feeItemMapper;
        this.ruleMapper = ruleMapper;
        this.billMapper = billMapper;
        this.houseMapper = houseMapper;
        this.calculator = calculator;
        this.idGen = idGen;
        this.jdbc = jdbc;
    }

    public List<MeterPoint> points() {
        return pointMapper.selectList(new LambdaQueryWrapper<MeterPoint>()
                .eq(MeterPoint::getStatus, "ENABLED").orderByAsc(MeterPoint::getId));
    }

    public MeterPoint savePoint(Long id, MeterPointCmd cmd) {
        MeterPoint p = id == null ? new MeterPoint() : pointMapper.selectById(id);
        if (p == null) {
            p = new MeterPoint();
            p.setId(idGen.nextId());
            p.setTenantId(TenantContext.tenantId());
            p.setCreateTime(LocalDateTime.now());
        }
        p.setSpaceId(cmd.spaceId());
        p.setFeeItemId(cmd.feeItemId());
        p.setMeterScope(cmd.meterScope() == null || cmd.meterScope().isBlank()
                ? "ROOM" : cmd.meterScope());
        p.setAllocationBasis(cmd.allocationBasis() == null || cmd.allocationBasis().isBlank()
                ? "PERSON_DAYS" : cmd.allocationBasis());
        p.setMeterName(cmd.meterName());
        p.setStatus(cmd.status() == null || cmd.status().isBlank() ? "ENABLED" : cmd.status());
        p.setUpdateTime(LocalDateTime.now());
        if (id == null) {
            pointMapper.insert(p);
        } else {
            pointMapper.updateById(p);
        }
        return p;
    }

    public void addReading(Long pointId, MeterReadCmd cmd) {
        MeterPoint p = pointMapper.selectById(pointId);
        if (p == null) {
            throw BizException.notFound("表计点位");
        }
        jdbc.update("insert into bp_fin_meter_point_reading"
                        + "(id,tenant_id,meter_point_id,reading,read_time,source,photo_url,remark,create_time)"
                        + " values(?,?,?,?,?,?,?,?,?)",
                idGen.nextId(), TenantContext.tenantId(), pointId, cmd.reading(),
                cmd.readTime() == null ? LocalDateTime.now() : cmd.readTime(),
                cmd.source() == null ? "MANUAL" : cmd.source(), cmd.photoUrl(), cmd.remark(),
                LocalDateTime.now());
    }

    /** 即时抄表：设备接口待接入，当前返回明确提示，由人工抄表兜底。 */
    public void readNow(Long pointId) {
        throw BizException.stateConflict("IoT read-now 接口待接入，请使用人工抄表");
    }

    public UtilityAllocationVO preview(String period, Long pointId) {
        List<MeterPoint> points = pointId == null ? points()
                : List.of(pointMapper.selectById(pointId));
        if (points.isEmpty() || points.get(0) == null) {
            throw BizException.notFound("表计点位");
        }
        MeterPoint p = points.get(0);
        return compute(p, period, false, null, null);
    }

    @Transactional(rollbackFor = Exception.class)
    public UtilityAllocationVO confirm(String period, Long pointId) {
        MeterPoint p = pointMapper.selectById(pointId);
        if (p == null) {
            throw BizException.notFound("表计点位");
        }
        Long dup = allocationMapper.selectCount(new LambdaQueryWrapper<UtilityAllocation>()
                .eq(UtilityAllocation::getMeterPointId, pointId)
                .eq(UtilityAllocation::getPeriod, period));
        if (dup != null && dup > 0) {
            throw BizException.stateConflict("该表计本期已分摊");
        }
        return compute(p, period, true, null, null);
    }

    /** 退租即时结算：截止日用量与分摊（按截至日人·天），结算后人员不再参与月终分摊。 */
    @Transactional(rollbackFor = Exception.class)
    public UtilityAllocationVO settleExit(Long pointId, Long contractId, LocalDate exitDate,
                                          BigDecimal exitReading) {
        MeterPoint p = pointMapper.selectById(pointId);
        if (p == null) {
            throw BizException.notFound("表计点位");
        }
        String period = YearMonth.from(exitDate).format(PERIOD);
        LocalDate monthStart = exitDate.withDayOfMonth(1);
        BigDecimal start = readingOnOrBefore(pointId, monthStart.atStartOfDay());
        if (start == null) {
            throw BizException.stateConflict("缺少月初读数，无法即时结算");
        }
        jdbc.update("insert into bp_fin_meter_point_reading"
                        + "(id,tenant_id,meter_point_id,reading,read_time,source,create_time)"
                        + " values(?,?,?,?,?,'MANUAL',?)",
                idGen.nextId(), TenantContext.tenantId(), pointId, exitReading,
                exitDate.atTime(23, 59), LocalDateTime.now());
        return computeExit(p, period, contractId, monthStart, exitDate, start, exitReading);
    }

    public List<UtilityAllocation> allocations(String period) {
        return allocationMapper.selectList(new LambdaQueryWrapper<UtilityAllocation>()
                .eq(period != null && !period.isBlank(), UtilityAllocation::getPeriod, period)
                .orderByDesc(UtilityAllocation::getId));
    }

    public EnergyStatVO energyMonthly(String period) {
        YearMonth ym = YearMonth.parse(period);
        BigDecimal total = BigDecimal.ZERO;
        BigDecimal sub = BigDecimal.ZERO;
        List<MeterPoint> points = pointMapper.selectList(new LambdaQueryWrapper<MeterPoint>()
                .eq(MeterPoint::getStatus, "ENABLED"));
        for (MeterPoint p : points) {
            BigDecimal usage = usageOf(p, ym);
            if (usage == null) {
                continue;
            }
            if ("BUILDING".equals(p.getMeterScope())) {
                total = total.add(usage);
            } else if ("ROOM".equals(p.getMeterScope())) {
                sub = sub.add(usage);
            }
        }
        BigDecimal diff = total.subtract(sub);
        BigDecimal rate = total.compareTo(BigDecimal.ZERO) <= 0 ? BigDecimal.ZERO
                : diff.divide(total, 4, RoundingMode.HALF_UP);
        EnergyPolicy policy = policy(null);
        BigDecimal warn = policy == null ? new BigDecimal("0.05") : policy.getWarnRate();
        BigDecimal alarm = policy == null ? new BigDecimal("0.10") : policy.getAlarmRate();
        String level = rate.compareTo(alarm) >= 0 ? "ALARM"
                : (rate.compareTo(warn) >= 0 ? "WARN" : "NORMAL");
        // 覆盖当月统计
        jdbc.update("delete from bp_fin_energy_monthly_stat where tenant_id=? and period=?",
                TenantContext.tenantId(), period);
        EnergyMonthlyStat st = new EnergyMonthlyStat();
        st.setId(idGen.nextId());
        st.setTenantId(TenantContext.tenantId());
        st.setPeriod(period);
        st.setTotalUsage(total);
        st.setSubmeterUsage(sub);
        st.setDiffUsage(diff);
        st.setDiffRate(rate);
        st.setAlertLevel(level);
        st.setCreateTime(LocalDateTime.now());
        statMapper.insert(st);
        return new EnergyStatVO(period, total, sub, diff, rate, level);
    }

    public EnergyPolicy policy(Long orgId) {
        List<EnergyPolicy> list = policyMapper.selectList(new LambdaQueryWrapper<EnergyPolicy>()
                .eq(EnergyPolicy::getStatus, "ENABLED"));
        EnergyPolicy fallback = null;
        for (EnergyPolicy p : list) {
            if (orgId != null && orgId.equals(p.getOrgId())) {
                return p;
            }
            if (p.getOrgId() == null) {
                fallback = p;
            }
        }
        return fallback;
    }

    public EnergyPolicy savePolicy(EnergyPolicyCmd cmd) {
        EnergyPolicy p = policy(cmd.orgId());
        boolean create = p == null || !java.util.Objects.equals(p.getOrgId(), cmd.orgId());
        if (create) {
            p = new EnergyPolicy();
            p.setId(idGen.nextId());
            p.setTenantId(TenantContext.tenantId());
            p.setOrgId(cmd.orgId());
            p.setCreateTime(LocalDateTime.now());
        }
        p.setVacancyBearer(cmd.vacancyBearer() == null ? "OPERATOR" : cmd.vacancyBearer());
        p.setWarnRate(cmd.warnRate() == null ? new BigDecimal("0.05") : cmd.warnRate());
        p.setAlarmRate(cmd.alarmRate() == null ? new BigDecimal("0.10") : cmd.alarmRate());
        p.setStatus("ENABLED");
        p.setUpdateTime(LocalDateTime.now());
        if (create) {
            policyMapper.insert(p);
        } else {
            policyMapper.updateById(p);
        }
        return p;
    }

    // ---------------- 计算 ----------------

    private UtilityAllocationVO compute(MeterPoint point, String period, boolean persist,
                                        Long onlyContract, LocalDate exitDate) {
        YearMonth ym = YearMonth.parse(period);
        BigDecimal start = readingOnOrBefore(point.getId(), ym.atDay(1).atStartOfDay());
        BigDecimal end = readingOnOrBefore(point.getId(), ym.atEndOfMonth().atTime(23, 59));
        if (start == null || end == null) {
            throw BizException.stateConflict("表计 " + point.getMeterName()
                    + " 缺少期初/期末读数，请先抄表");
        }
        BigDecimal usage = end.subtract(start);
        FinFeeItem item = feeItemMapper.selectById(point.getFeeItemId());
        if (item == null) {
            throw BizException.notFound("收费项目");
        }
        FinBillingRule rule = meterRule(item.getId(), ym);
        BillingCalculator.Result rr = calculator.calculate(item,
                BillingCalculator.Context.ofMeter(start, end), rule);
        BigDecimal totalAmount = rr.finalAmount();
        List<BizContract> contracts = contractsOf(point.getSpaceId(), ym);
        if (onlyContract != null) {
            contracts.removeIf(c -> !onlyContract.equals(c.getId()));
        }
        List<ShareDraft> drafts = new ArrayList<>();
        for (BizContract ct : contracts) {
            LocalDate os = ct.getLeaseStart() != null && ct.getLeaseStart().isAfter(ym.atDay(1))
                    ? ct.getLeaseStart() : ym.atDay(1);
            LocalDate oe = ct.getLeaseEnd() != null && ct.getLeaseEnd().isBefore(ym.atEndOfMonth())
                    ? ct.getLeaseEnd() : ym.atEndOfMonth();
            if (exitDate != null) {
                oe = oe.isAfter(exitDate) ? exitDate : oe;
            }
            if (os.isAfter(oe)) {
                continue;
            }
            int days = (int) ChronoUnit.DAYS.between(os, oe) + 1;
            Long co = cohabitantMapper.selectCount(new LambdaQueryWrapper<BizContractCohabitant>()
                    .eq(BizContractCohabitant::getContractId, ct.getId()));
            int persons = 1 + (co == null ? 0 : co.intValue());
            drafts.add(new ShareDraft(ct, days, BigDecimal.valueOf((long) days * persons)));
        }
        BigDecimal totalPd = drafts.stream().map(d -> d.personDays)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        BigDecimal allocated = BigDecimal.ZERO;
        for (ShareDraft d : drafts) {
            d.ratio = totalPd.compareTo(BigDecimal.ZERO) <= 0 ? BigDecimal.ZERO
                    : d.personDays.divide(totalPd, 8, RoundingMode.HALF_UP);
            d.amount = totalAmount.multiply(d.ratio).setScale(2, RoundingMode.HALF_UP);
            allocated = allocated.add(d.amount);
        }
        BigDecimal operator = totalAmount.subtract(allocated);
        EnergyPolicy policy = policy(null);
        boolean operatorBears = policy == null || "OPERATOR".equals(policy.getVacancyBearer());
        if (!operatorBears && drafts.size() > 0) {
            // 空床由在住租户承担：差额补给分摊额最大的一户
            drafts.sort(Comparator.comparing((ShareDraft d) -> d.amount).reversed());
            drafts.get(0).amount = drafts.get(0).amount.add(operator);
            operator = BigDecimal.ZERO;
        }
        BigDecimal finalOperator = operator;
        List<UtilityShareVO> vos = drafts.stream().map(d -> new UtilityShareVO(
                d.ct.getId(), d.ct.getContractNo(), d.ct.getLesseeName(),
                d.days, d.personDays, d.ratio, d.amount)).toList();
        Long allocationId = null;
        if (persist) {
            UtilityAllocation a = new UtilityAllocation();
            a.setId(idGen.nextId());
            a.setTenantId(TenantContext.tenantId());
            a.setMeterPointId(point.getId());
            a.setPeriod(period);
            a.setStartReading(start);
            a.setEndReading(end);
            a.setTotalUsage(usage);
            a.setTotalAmount(totalAmount);
            a.setOperatorBearAmount(finalOperator);
            a.setTierDetail(rr.explain());
            a.setStatus("CONFIRMED");
            a.setCreateTime(LocalDateTime.now());
            allocationMapper.insert(a);
            allocationId = a.getId();
            for (ShareDraft d : drafts) {
                UtilityShare s = new UtilityShare();
                s.setId(idGen.nextId());
                s.setTenantId(TenantContext.tenantId());
                s.setAllocationId(a.getId());
                s.setContractId(d.ct.getId());
                s.setPersonId(d.ct.getLesseePersonId());
                s.setOccupyDays(d.days);
                s.setPersonDays(d.personDays);
                s.setShareRatio(d.ratio);
                s.setShareAmount(d.amount);
                s.setRoundingDelta(BigDecimal.ZERO);
                shareMapper.insert(s);
                if (d.amount.compareTo(BigDecimal.ZERO) > 0) {
                    FinBill b = new FinBill();
                    b.setId(idGen.nextId());
                    b.setTenantId(TenantContext.tenantId());
                    b.setBillNo("FB" + b.getId());
                    b.setOrgId(d.ct.getOrgId());
                    b.setContractId(d.ct.getId());
                    b.setHouseId(d.ct.getHouseId());
                    b.setSpaceId(d.ct.getSpaceId());
                    b.setPersonId(d.ct.getLesseePersonId());
                    b.setPayerName(d.ct.getLesseeName());
                    b.setPayerPhone(d.ct.getLesseePhone());
                    b.setFeeItemId(item.getId());
                    b.setBillPeriod(period);
                    b.setPeriodStart(ym.atDay(1));
                    b.setPeriodEnd(ym.atEndOfMonth());
                    b.setBillAmount(d.amount);
                    b.setDiscountAmount(BigDecimal.ZERO);
                    b.setLateFee(BigDecimal.ZERO);
                    b.setPaidAmount(BigDecimal.ZERO);
                    b.setWaivedAmount(BigDecimal.ZERO);
                    b.setPayableAmount(d.amount);
                    b.setDueDate(ym.atEndOfMonth());
                    b.setBillStatus("UNPAID");
                    b.setOverdueDays(0);
                    b.setGenerateType("AUTO");
                    b.setBillingQuantity(d.days);
                    b.setQuantityUnit("PERSON_DAY");
                    b.setQuantitySource("ALLOCATION");
                    b.setTierDetail(rr.explain());
                    b.setRemark("能耗分摊：" + point.getMeterName() + "；人·天 "
                            + d.personDays.stripTrailingZeros().toPlainString() + "/"
                            + totalPd.stripTrailingZeros().toPlainString());
                    b.setIsDeleted(0);
                    b.setCreateTime(LocalDateTime.now());
                    billMapper.insert(b);
                    s.setBillId(b.getId());
                    shareMapper.updateById(s);
                }
            }
        }
        return new UtilityAllocationVO(allocationId, point.getId(), point.getMeterName(),
                period, start, end, usage, totalAmount, finalOperator, vos);
    }

    private UtilityAllocationVO computeExit(MeterPoint point, String period, Long contractId,
                                            LocalDate monthStart, LocalDate exitDate,
                                            BigDecimal start, BigDecimal exitReading) {
        BigDecimal usage = exitReading.subtract(start);
        FinFeeItem item = feeItemMapper.selectById(point.getFeeItemId());
        BillingCalculator.Result rr = calculator.calculate(item,
                BillingCalculator.Context.ofMeter(start, exitReading), meterRule(item.getId(),
                        YearMonth.from(exitDate)));
        List<BizContract> contracts = contractsOf(point.getSpaceId(), YearMonth.from(exitDate));
        BigDecimal totalPd = BigDecimal.ZERO;
        List<ShareDraft> drafts = new ArrayList<>();
        for (BizContract ct : contracts) {
            LocalDate os = ct.getLeaseStart() != null && ct.getLeaseStart().isAfter(monthStart)
                    ? ct.getLeaseStart() : monthStart;
            LocalDate oe = ct.getLeaseEnd() != null && ct.getLeaseEnd().isBefore(exitDate)
                    ? ct.getLeaseEnd() : exitDate;
            if (os.isAfter(oe)) {
                continue;
            }
            int days = (int) ChronoUnit.DAYS.between(os, oe) + 1;
            Long co = cohabitantMapper.selectCount(new LambdaQueryWrapper<BizContractCohabitant>()
                    .eq(BizContractCohabitant::getContractId, ct.getId()));
            int persons = 1 + (co == null ? 0 : co.intValue());
            BigDecimal pd = BigDecimal.valueOf((long) days * persons);
            drafts.add(new ShareDraft(ct, days, pd));
            totalPd = totalPd.add(pd);
        }
        ShareDraft target = drafts.stream().filter(d -> d.ct.getId().equals(contractId))
                .findFirst().orElseThrow(() -> BizException.notFound("合同"));
        BigDecimal ratio = totalPd.compareTo(BigDecimal.ZERO) <= 0 ? BigDecimal.ZERO
                : target.personDays.divide(totalPd, 8, RoundingMode.HALF_UP);
        BigDecimal amount = rr.finalAmount().multiply(ratio).setScale(2, RoundingMode.HALF_UP);
        UtilityAllocation a = new UtilityAllocation();
        a.setId(idGen.nextId());
        a.setTenantId(TenantContext.tenantId());
        a.setMeterPointId(point.getId());
        a.setPeriod(period + "-EXIT-" + contractId);
        a.setStartReading(start);
        a.setEndReading(exitReading);
        a.setTotalUsage(usage);
        a.setTotalAmount(amount);
        a.setOperatorBearAmount(BigDecimal.ZERO);
        a.setTierDetail(rr.explain());
        a.setStatus("EXIT");
        a.setCreateTime(LocalDateTime.now());
        allocationMapper.insert(a);
        UtilityShare s = new UtilityShare();
        s.setId(idGen.nextId());
        s.setTenantId(TenantContext.tenantId());
        s.setAllocationId(a.getId());
        s.setContractId(contractId);
        s.setPersonId(target.ct.getLesseePersonId());
        s.setOccupyDays(target.days);
        s.setPersonDays(target.personDays);
        s.setShareRatio(ratio);
        s.setShareAmount(amount);
        s.setRoundingDelta(BigDecimal.ZERO);
        shareMapper.insert(s);
        return new UtilityAllocationVO(a.getId(), point.getId(), point.getMeterName(),
                period, start, exitReading, usage, amount, BigDecimal.ZERO,
                List.of(new UtilityShareVO(target.ct.getId(), target.ct.getContractNo(),
                        target.ct.getLesseeName(), target.days, target.personDays, ratio, amount)));
    }

    private List<BizContract> contractsOf(Long spaceId, YearMonth ym) {
        if (spaceId == null) {
            return new ArrayList<>();
        }
        LocalDate start = ym.atDay(1);
        LocalDate end = ym.atEndOfMonth();
        return new ArrayList<>(contractMapper.selectList(new LambdaQueryWrapper<BizContract>()
                .eq(BizContract::getSpaceId, spaceId)
                .ne(BizContract::getContractStatus, ContractStatus.DRAFT.name())
                .le(BizContract::getLeaseStart, end)
                .ge(BizContract::getLeaseEnd, start)));
    }

    private BigDecimal readingOnOrBefore(Long pointId, LocalDateTime time) {
        List<BigDecimal> list = jdbc.queryForList(
                "select reading from bp_fin_meter_point_reading where meter_point_id=?"
                        + " and read_time<=? order by read_time desc, id desc limit 1",
                BigDecimal.class, pointId, time);
        return list.isEmpty() ? null : list.get(0);
    }

    private BigDecimal usageOf(MeterPoint p, YearMonth ym) {
        BigDecimal s = readingOnOrBefore(p.getId(), ym.atDay(1).atStartOfDay());
        BigDecimal e = readingOnOrBefore(p.getId(), ym.atEndOfMonth().atTime(23, 59));
        if (s == null || e == null) {
            return null;
        }
        return e.subtract(s);
    }

    private FinBillingRule meterRule(Long feeItemId, YearMonth ym) {
        List<FinBillingRule> rules = ruleMapper.selectList(new LambdaQueryWrapper<FinBillingRule>()
                .eq(FinBillingRule::getFeeItemId, feeItemId)
                .eq(FinBillingRule::getStatus, "ENABLED")
                .eq(FinBillingRule::getApproveStatus, "APPROVED")
                .eq(FinBillingRule::getIsDeleted, 0)
                .orderByDesc(FinBillingRule::getPriority));
        for (FinBillingRule r : rules) {
            if (r.getEffectiveStart() != null && r.getEffectiveStart().isAfter(ym.atEndOfMonth())) {
                continue;
            }
            if (r.getEffectiveEnd() != null && r.getEffectiveEnd().isBefore(ym.atDay(1))) {
                continue;
            }
            return r;
        }
        return null;
    }

    private static class ShareDraft {
        final BizContract ct;
        final int days;
        final BigDecimal personDays;
        BigDecimal ratio = BigDecimal.ZERO;
        BigDecimal amount = BigDecimal.ZERO;

        ShareDraft(BizContract ct, int days, BigDecimal personDays) {
            this.ct = ct;
            this.days = days;
            this.personDays = personDays;
        }
    }
}
'''

files['controller/UtilityAllocationController.java'] = '''package com.yundao.bp.fin.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.fin.dto.*;
import com.yundao.bp.fin.entity.EnergyPolicy;
import com.yundao.bp.fin.entity.MeterPoint;
import com.yundao.bp.fin.entity.UtilityAllocation;
import com.yundao.bp.fin.service.UtilityAllocationService;
import jakarta.validation.Valid;
import java.time.LocalDate;
import java.util.List;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/fin")
public class UtilityAllocationController {

    private final UtilityAllocationService service;

    public UtilityAllocationController(UtilityAllocationService service) {
        this.service = service;
    }

    @GetMapping("/meter-points")
    public R<List<MeterPoint>> points() {
        return R.ok(service.points());
    }

    @PostMapping("/meter-points")
    public R<MeterPoint> createPoint(@Valid @RequestBody MeterPointCmd cmd) {
        return R.ok(service.savePoint(null, cmd));
    }

    @PutMapping("/meter-points/{id}")
    public R<MeterPoint> updatePoint(@PathVariable Long id,
                                     @Valid @RequestBody MeterPointCmd cmd) {
        return R.ok(service.savePoint(id, cmd));
    }

    @PostMapping("/meter-points/{id}/readings")
    public R<Void> addReading(@PathVariable Long id, @RequestBody MeterReadCmd cmd) {
        service.addReading(id, cmd);
        return R.ok(null);
    }

    @PostMapping("/meter-points/{id}/read-now")
    public R<Void> readNow(@PathVariable Long id) {
        service.readNow(id);
        return R.ok(null);
    }

    @PostMapping("/utility-allocations/preview")
    public R<UtilityAllocationVO> preview(@RequestBody AllocCmd cmd) {
        return R.ok(service.preview(cmd.period(), cmd.meterPointId()));
    }

    @PostMapping("/utility-allocations/confirm")
    public R<UtilityAllocationVO> confirm(@RequestBody AllocCmd cmd) {
        return R.ok(service.confirm(cmd.period(), cmd.meterPointId()));
    }

    @PostMapping("/utility-allocations/exit")
    public R<UtilityAllocationVO> exit(@RequestBody ExitCmd cmd) {
        return R.ok(service.settleExit(cmd.meterPointId(), cmd.contractId(), cmd.exitDate(),
                cmd.reading()));
    }

    @GetMapping("/utility-allocations")
    public R<List<UtilityAllocation>> allocations(@RequestParam(required = false) String period) {
        return R.ok(service.allocations(period));
    }

    @GetMapping("/energy-analysis/monthly")
    public R<EnergyStatVO> monthly(@RequestParam String period) {
        return R.ok(service.energyMonthly(period));
    }

    @GetMapping("/energy-policy")
    public R<EnergyPolicy> policy(@RequestParam(required = false) Long orgId) {
        return R.ok(service.policy(orgId));
    }

    @PutMapping("/energy-policy")
    public R<EnergyPolicy> savePolicy(@RequestBody EnergyPolicyCmd cmd) {
        return R.ok(service.savePolicy(cmd));
    }

    public record AllocCmd(String period, Long meterPointId) {
    }

    public record ExitCmd(Long meterPointId, Long contractId, LocalDate exitDate,
                          java.math.BigDecimal reading) {
    }
}
'''

for rel, code in files.items():
    p = os.path.join(BASE, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, 'w', encoding='utf-8', newline='').write(code)
print('utility service/controller written')
