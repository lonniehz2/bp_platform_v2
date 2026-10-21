package com.yundao.bp.fin.constant;

/**
 * 计费方式（对应 {@code bp_fin_fee_item.calc_mode}）。
 *
 * <p>⭐ <b>多业态支持的关键</b>：不同业态用不同计费方式——
 * <ul>
 *   <li>保障房/长租公寓：{@link #BY_AREA} 按面积、{@link #BY_HOUSE} 按套、{@link #BY_BED} 按床位</li>
 *   <li>宿舍：{@link #BY_BED} 按床位</li>
 *   <li>酒店/民宿/网约房：{@link #BY_NIGHT} 按夜</li>
 *   <li>园区/物业能耗费：{@link #METER} 按抄表</li>
 * </ul>
 */
public enum CalcMode {

    FIXED("固定额"),
    BY_AREA("按面积"),
    BY_HOUSE("按套"),
    BY_PERSON("按人"),
    BY_BED("按床位"),
    BY_NIGHT("按夜"),
    METER("按抄表");

    private final String label;

    CalcMode(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 是否需要面积参与计算。 */
    public boolean needsArea() {
        return this == BY_AREA;
    }

    /** 是否需要数量（人数/床数/天数）参与计算。 */
    public boolean needsQuantity() {
        return this == BY_PERSON || this == BY_BED || this == BY_NIGHT;
    }

    /** 是否需要抄表读数（本次读数 - 上次读数）。 */
    public boolean needsMeter() {
        return this == METER;
    }
}
