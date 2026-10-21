package com.yundao.bp.fin.constant;

/**
 * 欠费处置动作（对应 {@code bp_fin_arrears_action.action_type}）。
 */
public enum ArrearsActionType {

    NOTIFY("通知催缴"),
    FREEZE("冻结权限"),
    UNFREEZE("解冻"),
    RESTRICT("限制续租"),
    EXPIRE("到期不续"),
    LEGAL("司法程序");

    private final String label;

    ArrearsActionType(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 是否需要联动授权模块。 */
    public boolean touchesGrant() {
        return this == FREEZE || this == UNFREEZE;
    }
}
