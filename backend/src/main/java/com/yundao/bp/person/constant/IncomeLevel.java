package com.yundao.bp.person.constant;

import java.math.BigDecimal;

/**
 * 收入档位。
 *
 * <p><b>为什么做成枚举+阈值可配</b>：各地低保线/中低收入线不同，
 * 且会逐年调整。阈值由调用方传入（来自系统参数），本枚举只负责<b>判定规则</b>，
 * 保证「同一套判定逻辑，不同地区不同阈值」。
 */
public enum IncomeLevel {

    LOW("低保"),
    LOW_INCOME("低收入"),
    MIDDLE_LOW("中低收入"),
    NORMAL("普通");

    private final String label;

    IncomeLevel(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /**
     * 按人均月收入判定档位。
     *
     * @param monthlyIncome   家庭月收入（元）
     * @param familySize      家庭人口
     * @param lowLine         低保线（人均月收入）
     * @param lowIncomeLine   低收入线
     * @param middleLowLine   中低收入线
     */
    public static IncomeLevel of(BigDecimal monthlyIncome, Integer familySize,
                                 BigDecimal lowLine, BigDecimal lowIncomeLine,
                                 BigDecimal middleLowLine) {
        if (monthlyIncome == null) {
            return NORMAL;
        }
        int size = (familySize == null || familySize <= 0) ? 1 : familySize;
        BigDecimal perCapita = monthlyIncome.divide(BigDecimal.valueOf(size), 2,
                java.math.RoundingMode.HALF_UP);
        if (lowLine != null && perCapita.compareTo(lowLine) <= 0) {
            return LOW;
        }
        if (lowIncomeLine != null && perCapita.compareTo(lowIncomeLine) <= 0) {
            return LOW_INCOME;
        }
        if (middleLowLine != null && perCapita.compareTo(middleLowLine) <= 0) {
            return MIDDLE_LOW;
        }
        return NORMAL;
    }
}
