package com.yundao.bp.biz.constant;

/**
 * 惩戒措施（对应 {@code bp_biz_credit_record.sanction_type}）。
 */
public enum SanctionType {

    TERMINATE("终止资格"),
    BAN_APPLY("限制申请"),
    CREDIT_PLATFORM("推送信用平台"),
    FINE("罚款"),
    OTHER("其他");

    private final String label;

    SanctionType(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 是否需计算限制申请年限。 */
    public boolean needsBanYears() {
        return this == BAN_APPLY;
    }
}
