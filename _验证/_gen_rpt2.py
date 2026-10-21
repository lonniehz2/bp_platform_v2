# -*- coding: utf-8 -*-
"""生成报表/大屏服务 + 接口（含真实指标聚合与 CSV 导出）"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
F = {}

F['rpt/service/ReportService.java'] = '''package com.yundao.bp.rpt.service;

import com.yundao.bp.rpt.dto.ExportTaskVO;
import com.yundao.bp.rpt.dto.ReportQueryCmd;
import com.yundao.bp.rpt.dto.ReportResultVO;
import com.yundao.bp.rpt.entity.RptReportDef;
import java.util.List;

/**
 * 报表服务：定义管理 + 查询执行 + 异步导出。
 */
public interface ReportService {

    /** 报表定义列表。 */
    List<RptReportDef> listReports(String reportType);

    /** 按定义查询数据（分页）。 */
    ReportResultVO query(ReportQueryCmd cmd);

    /** 创建并<b>同步执行</b>导出任务（生成 CSV 文件）。 */
    ExportTaskVO export(ReportQueryCmd cmd, Long userId);

    ExportTaskVO getTask(Long id);

    List<ExportTaskVO> listTasks(Long userId);

    /** 执行待处理任务（供定时任务/手动触发）。 */
    int runPendingTasks();

    /** 读取导出文件文本内容（供下载接口用）。 */
    String readFile(Long taskId);
}
'''

F['rpt/service/ScreenService.java'] = '''package com.yundao.bp.rpt.service;

import com.yundao.bp.rpt.entity.RptScreenDef;
import java.util.List;
import java.util.Map;

/**
 * 大屏服务：可配置大屏定义 + 实时数据。
 */
public interface ScreenService {

    List<RptScreenDef> listScreens(String screenType);

    RptScreenDef getByCode(String screenCode);

    /**
     * 取大屏数据（按 widget 配置逐项取指标）。
     *
     * @return { screen: 定义, widgets: [ {code,title,chart,value,unit} ] }
     */
    Map<String, Object> data(String screenCode, Long orgId);

    RptScreenDef save(String screenCode, String screenName, String screenType,
                      String layoutConfig, String widgetConfig, Integer refreshSeconds);
}
'''

F['rpt/service/MetricService.java'] = '''package com.yundao.bp.rpt.service;

import com.yundao.bp.rpt.entity.RptMetricDaily;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;

/**
 * 指标服务：从业务表实时聚合 + 日快照。
 */
public interface MetricService {

    /** 实时取单个指标值。 */
    double current(String metricCode, Long orgId);

    /** 实时取全部指标（驾驶舱/大屏用）。 */
    Map<String, Object> currentAll(Long orgId);

    /** 把今日指标落成日快照（供趋势图）。 */
    int snapshotToday(Long orgId);

    /** 指标趋势（按日）。 */
    List<RptMetricDaily> trend(String metricCode, Long orgId, LocalDate from, LocalDate to);
}
'''

F['rpt/service/impl/MetricServiceImpl.java'] = '''package com.yundao.bp.rpt.service.impl;

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
            case "BILL_UNPAID_COUNT" -> count(billMapper.selectCount(
                    new LambdaQueryWrapper<FinBill>()
                            .eq(orgId != null, FinBill::getOrgId, orgId)
                            .in(FinBill::getBillStatus,
                                    List.of("UNPAID", "PARTIAL", "OVERDUE"))));
            case "BILL_UNPAID_AMOUNT" -> sum(billMapper.selectList(
                    new LambdaQueryWrapper<FinBill>()
                            .eq(orgId != null, FinBill::getOrgId, orgId)
                            .in(FinBill::getBillStatus,
                                    List.of("UNPAID", "PARTIAL", "OVERDUE"))));
            case "PAYMENT_TOTAL_AMOUNT" -> sumPayments(orgId);
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

    private static double sum(List<FinBill> bills) {
        BigDecimal s = BigDecimal.ZERO;
        for (FinBill b : bills) {
            s = s.add(b.getPayableAmount() == null ? BigDecimal.ZERO : b.getPayableAmount());
        }
        return s.setScale(2, RoundingMode.HALF_UP).doubleValue();
    }

    private double sumPayments(Long orgId) {
        List<FinPayment> list = paymentMapper.selectList(
                new LambdaQueryWrapper<FinPayment>()
                        .eq(orgId != null, FinPayment::getOrgId, orgId)
                        .eq(FinPayment::getPayStatus, "SUCCESS"));
        BigDecimal s = BigDecimal.ZERO;
        for (FinPayment p : list) {
            s = s.add(p.getPayAmount() == null ? BigDecimal.ZERO : p.getPayAmount());
        }
        return s.setScale(2, RoundingMode.HALF_UP).doubleValue();
    }
}
'''

count = 0
for rel, content in F.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个文件' % count)
