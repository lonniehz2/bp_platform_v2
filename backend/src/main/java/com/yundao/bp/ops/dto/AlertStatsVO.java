package com.yundao.bp.ops.dto;

import java.util.Map;

/**
 * 告警统计（驾驶舱 / 大屏用）。
 *
 * @param total      总数
 * @param pending    待处理（PENDING + ESCALATED）
 * @param handling   处理中
 * @param handled    已闭环
 * @param ignored    误报忽略
 * @param byLevel    按级别分布
 * @param byCategory 按类别分布
 * @param urgentOpen 紧急且未闭环 —— 大屏红色告警数
 */
public record AlertStatsVO(
        long total,
        long pending,
        long handling,
        long handled,
        long ignored,
        Map<String, Long> byLevel,
        Map<String, Long> byCategory,
        long urgentOpen
) {
}
