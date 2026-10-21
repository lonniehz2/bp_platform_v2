package com.yundao.bp.biz.constant;

/**
 * 复议结果影响（对应 {@code bp_biz_appeal.result_effect}）。
 *
 * <p>⭐ 这是复议<b>真正产生后果</b>的字段：维持原结论 / 恢复资格 / 取消资格 / 调整标准。
 */
public enum AppealResultEffect {

    RESTORE("恢复资格"),
    CANCEL("取消资格"),
    ADJUST("调整标准"),
    NONE("无影响");

    private final String label;

    AppealResultEffect(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 是否改变了原结论。 */
    public boolean changesOutcome() {
        return this != NONE;
    }
}
