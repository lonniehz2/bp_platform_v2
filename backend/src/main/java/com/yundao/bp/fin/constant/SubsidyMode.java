package com.yundao.bp.fin.constant;

/**
 * 补贴方式（对应 {@code bp_fin_subsidy_standard.subsidy_mode}）。
 *
 * <p>⭐ <b>广州"实物配租 + 租赁补贴"双轨</b>的核心：不同人群用不同方式算补贴。
 *
 * <pre>
 *   FIXED   定额     ：每月固定金额（如低保户 800 元/月）
 *   BY_AREA 按面积   ：补贴单价 × 建筑面积（如 20 元/㎡·月）
 *   BY_PERSON按人    ：人均补贴 × 家庭人口（如 300 元/人·月）
 *   RATIO   按租金比例：实际租金 × 比例（如补贴 60% 市场租金）
 * </pre>
 *
 * <p>所有方式算完后统一受 {@code max_amount}（单户月度封顶）约束。
 */
public enum SubsidyMode {

    FIXED("定额"),
    BY_AREA("按面积"),
    BY_PERSON("按人"),
    RATIO("按租金比例");

    private final String label;

    SubsidyMode(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 是否需要面积参与。 */
    public boolean needsArea() {
        return this == BY_AREA;
    }

    /** 是否需要家庭人口参与。 */
    public boolean needsPersonCount() {
        return this == BY_PERSON;
    }

    /** 是否需要月租金参与。 */
    public boolean needsRent() {
        return this == RATIO;
    }
}
