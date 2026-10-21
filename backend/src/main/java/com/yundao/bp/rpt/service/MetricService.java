package com.yundao.bp.rpt.service;

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

    /**
     * 按需取指定指标（只算传入的编码，不算无用指标）。
     *
     * <p>大屏组件通常只用一部分指标，按需取可显著减少查询轮次。
     */
    Map<String, Object> values(java.util.List<String> codes, Long orgId);

    /** 把今日指标落成日快照（供趋势图）。 */
    int snapshotToday(Long orgId);

    /** 指标趋势（按日）。 */
    List<RptMetricDaily> trend(String metricCode, Long orgId, LocalDate from, LocalDate to);
}
