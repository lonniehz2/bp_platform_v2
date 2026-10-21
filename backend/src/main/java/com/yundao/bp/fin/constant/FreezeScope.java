package com.yundao.bp.fin.constant;

/**
 * 冻结范围（对应 {@code bp_fin_arrears_action.freeze_scope}）。
 *
 * <p>⭐⭐ <b>安全底线（决策 D19）</b>：欠费停权<b>不得停用大门门禁</b>。
 * 原因：
 * <ul>
 *   <li><b>消防与应急逃生</b>：大门是唯一疏散通道，停用会造成安全隐患甚至法律责任</li>
 *   <li><b>基本居住权</b>：房门锁停用已足以施压，停大门等于剥夺基本生活与进出权利</li>
 *   <li><b>合规要求</b>：多地保障房管理办法明确不得以欠费为由影响居住安全</li>
 * </ul>
 *
 * <p>因此系统默认且推荐 {@link #EXCLUDE_MAIN_DOOR}；
 * {@link #ALL} 需显式确认风险才能使用，且会被记录审计。
 */
public enum FreezeScope {

    /** 全部设备（含大门）—— 默认禁止，需显式确认风险 */
    ALL("全部设备（含大门）", true),
    /** 仅房门锁 —— 过度收窄，可能影响正常进出楼道 */
    ROOM_LOCK("仅房门锁", false),
    /** 排除大门门禁 —— ⭐ 推荐与默认，安全底线 */
    EXCLUDE_MAIN_DOOR("排除大门门禁（安全底线）", false);

    private final String label;
    private final boolean risky;

    FreezeScope(String label, boolean risky) {
        this.label = label;
        this.risky = risky;
    }

    public String label() {
        return label;
    }

    /** 是否属于有安全风险的范围（需人工确认）。 */
    public boolean risky() {
        return risky;
    }
}
