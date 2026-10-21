package com.yundao.bp.biz.constant;

/**
 * 公示类型（对应 {@code bp_biz_publicity.publicity_type}）。
 */
public enum PublicityType {

    QUALIFY("资格公示"),
    ALLOCATION("配租公示"),
    EXIT("退出公示");

    private final String label;

    PublicityType(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }
}
