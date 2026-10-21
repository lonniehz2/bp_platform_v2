package com.yundao.bp.rpt.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.asset.entity.AssetHouse;
import com.yundao.bp.asset.mapper.AssetHouseMapper;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.dev.entity.DevAccessRecord;
import com.yundao.bp.dev.mapper.DevAccessRecordMapper;
import com.yundao.bp.fin.entity.FinBill;
import com.yundao.bp.fin.entity.FinPayment;
import com.yundao.bp.fin.mapper.FinBillMapper;
import com.yundao.bp.fin.mapper.FinPaymentMapper;
import com.yundao.bp.rpt.entity.RptMetricDaily;
import com.yundao.bp.rpt.mapper.RptMetricDailyMapper;
import com.yundao.bp.rpt.service.MetricService;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 指标实现：直接从业务表实时聚合（无需预计算即可用），
 * 同时支持落日快照用于趋势。
 */
@Service
public class MetricServiceImpl implements MetricService {

    private static final Logger log = LoggerFactory.getLogger(MetricServiceImpl.class);

    private final AssetHouseMapper houseMapper;
    private final FinBillMapper billMapper;
    private final FinPaymentMapper paymentMapper;
    private final DevAccessRecordMapper accessMapper;
    private final RptMetricDailyMapper dailyMapper;
    private final SnowflakeIdGenerator idGen;

    public MetricServiceImpl(AssetHouseMapper houseMapper, FinBillMapper billMapper,
                             FinPaymentMapper paymentMapper, DevAccessRecordMapper accessMapper,
                             RptMetricDailyMapper dailyMapper, SnowflakeIdGenerator idGen) {
        this.houseMapper = houseMapper;
        this.billMapper = billMapper;
        this.paymentMapper = paymentMapper;
        this.accessMapper = accessMapper;
        this.dailyMapper = dailyMapper;
        this.idGen = idGen;
    }

    @Override
    public double current(String metricCode, Long orgId) {
        return switch (metricCode) {
            case "HOUSE_TOTAL" -> count(houseMapper.selectCount(
                    new LambdaQueryWrapper<AssetHouse>()
                            .eq(orgId != null, AssetHouse::getOrgId, orgId)));
            case "HOUSE_OCCUPIED" -> count(houseMapper.selectCount(
                    new LambdaQueryWrapper<AssetHouse>()
                            .eq(orgId != null, AssetHouse::getOrgId, orgId)
                            .in(AssetHouse::getHouseStatus, List.of("OCCUPIED", "ALLOCATED"))));
            case "HOUSE_VACANT" -> count(houseMapper.selectCount(
                    new LambdaQueryWrapper<AssetHouse>()
                            .eq(orgId != null, AssetHouse::getOrgId, orgId)
                            .in(AssetHouse::getHouseStatus, List.of("VACANT", "PENDING_ALLOC"))));
            case "OCCUPANCY_RATE" -> {
                double total = current("HOUSE_TOTAL", orgId);
                double occ = current("HOUSE_OCCUPIED", orgId);
                yield total == 0 ? 0.0
                        : Math.round(occ * 10000.0 / total) / 100.0;
            }
            case "BILL_UNPAID_COUNT" -> count(billMapper.countUnpaid(
                    TenantContext.tenantId(), orgId));
            case "BILL_UNPAID_AMOUNT" -> money(billMapper.sumUnpaidPayable(
                    TenantContext.tenantId(), orgId));
            case "PAYMENT_TOTAL_AMOUNT" -> money(paymentMapper.sumSuccessPayAmount(
                    TenantContext.tenantId(), orgId));
            case "ACCESS_TODAY_COUNT" -> count(accessMapper.selectCount(
                    new LambdaQueryWrapper<DevAccessRecord>()
                            .eq(orgId != null, DevAccessRecord::getOrgId, orgId)
                            .ge(DevAccessRecord::getOpenTime, LocalDate.now().atStartOfDay())));
            case "ACCESS_ABNORMAL_COUNT" -> count(accessMapper.selectCount(
                    new LambdaQueryWrapper<DevAccessRecord>()
                            .eq(orgId != null, DevAccessRecord::getOrgId, orgId)
                            .eq(DevAccessRecord::getIsAbnormal, 1)
                            .ge(DevAccessRecord::getOpenTime, LocalDate.now().atStartOfDay())));
            default -> 0.0;
        };
    }

    @Override
    public Map<String, Object> currentAll(Long orgId) {
        Map<String, Object> m = new LinkedHashMap<>();
        for (String code : List.of("HOUSE_TOTAL", "HOUSE_OCCUPIED", "HOUSE_VACANT",
                "OCCUPANCY_RATE", "BILL_UNPAID_COUNT", "BILL_UNPAID_AMOUNT",
                "PAYMENT_TOTAL_AMOUNT", "ACCESS_TODAY_COUNT", "ACCESS_ABNORMAL_COUNT")) {
            m.put(code, current(code, orgId));
        }
        m.put("generatedAt", LocalDateTime.now().toString());
        return m;
    }

    @Override
    public Map<String, Object> values(java.util.List<String> codes, Long orgId) {
        Map<String, Object> m = new LinkedHashMap<>();
        for (String code : codes) {
            m.put(code, current(code, orgId));
        }
        return m;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int snapshotToday(Long orgId) {
        LocalDate today = LocalDate.now();
        int n = 0;
        for (String code : List.of("HOUSE_TOTAL", "HOUSE_OCCUPIED", "HOUSE_VACANT",
                "OCCUPANCY_RATE", "BILL_UNPAID_COUNT", "BILL_UNPAID_AMOUNT",
                "PAYMENT_TOTAL_AMOUNT", "ACCESS_TODAY_COUNT", "ACCESS_ABNORMAL_COUNT")) {
            double v = current(code, orgId);
            RptMetricDaily exist = dailyMapper.selectOne(
                    new LambdaQueryWrapper<RptMetricDaily>()
                            .eq(RptMetricDaily::getStatDate, today)
                            .eq(RptMetricDaily::getMetricCode, code)
                            .eq(orgId != null, RptMetricDaily::getOrgId, orgId)
                            .last("LIMIT 1"));
            if (exist != null) {
                exist.setMetricValue(BigDecimal.valueOf(v).setScale(4, RoundingMode.HALF_UP));
                exist.setUpdateTime(LocalDateTime.now());
                dailyMapper.updateById(exist);
            } else {
                RptMetricDaily d = new RptMetricDaily();
                d.setId(idGen.nextId());
                d.setTenantId(TenantContext.tenantId());
                d.setStatDate(today);
                d.setOrgId(orgId);
                d.setMetricCode(code);
                d.setMetricName(code);
                d.setMetricValue(BigDecimal.valueOf(v).setScale(4, RoundingMode.HALF_UP));
                d.setCreateTime(LocalDateTime.now());
                d.setUpdateTime(LocalDateTime.now());
                dailyMapper.insert(d);
            }
            n++;
        }
        log.info("指标日快照完成：{} 条（orgId={}）", n, orgId);
        return n;
    }

    @Override
    public List<RptMetricDaily> trend(String metricCode, Long orgId, LocalDate from,
                                      LocalDate to) {
        LambdaQueryWrapper<RptMetricDaily> qw = new LambdaQueryWrapper<RptMetricDaily>()
                .eq(RptMetricDaily::getMetricCode, metricCode)
                .eq(orgId != null, RptMetricDaily::getOrgId, orgId)
                .orderByAsc(RptMetricDaily::getStatDate);
        if (from != null) {
            qw.ge(RptMetricDaily::getStatDate, from);
        }
        if (to != null) {
            qw.le(RptMetricDaily::getStatDate, to);
        }
        return dailyMapper.selectList(qw);
    }

    private static double count(Long n) {
        return n == null ? 0 : n;
    }

    private static double money(BigDecimal v) {
        return (v == null ? BigDecimal.ZERO : v)
                .setScale(2, RoundingMode.HALF_UP).doubleValue();
    }
}
