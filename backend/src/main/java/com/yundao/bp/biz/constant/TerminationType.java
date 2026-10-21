package com.yundao.bp.biz.constant;

/**
 * 退租类型（对应 {@code bp_biz_termination.termination_type}）。
 *
 * <p>不同类型决定政策口径：
 * {@code EXPEL 违规清退} 需写 {@code ban_reapply_end_date}（如 5 年内不得再申请）。
 */
public enum TerminationType {

    NORMAL("正常退租"),
    EXPEL("违规清退"),
    EXPIRE("到期不续"),
    EXCHANGE("换房退出"),
    OTHER("其他");

    private final String label;

    TerminationType(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }
}
