package com.yundao.bp.biz.constant;

/**
 * 摇号/选房结果类型（对应 {@code bp_biz_lottery_result.result_type}）。
 */
public enum LotteryResultType {

    WON("中签"),
    LOST("未中签"),
    WAITLIST("递补"),
    GIVE_UP("放弃");

    private final String label;

    LotteryResultType(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 是否具备配租资格。 */
    public boolean canAllocate() {
        return this == WON || this == WAITLIST;
    }
}
