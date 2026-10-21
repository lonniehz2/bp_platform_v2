package com.yundao.bp.biz.constant;

/**
 * 违规类型（对应 {@code bp_biz_credit_record.violation_type}）。
 */
public enum ViolationType {

    FALSE_INFO("提供虚假信息"),
    SUBLEASE("转租出借"),
    STRUCTURE("破坏结构"),
    CHANGE_USE("改变用途"),
    VACANT("长期空置"),
    ILLEGAL("从事违法活动"),
    ARREARS("恶意欠租"),
    OTHER("其他");

    private final String label;

    ViolationType(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 是否属于严重违规（默认需限制申请年限）。 */
    public boolean severe() {
        return this == FALSE_INFO || this == SUBLEASE || this == ILLEGAL
                || this == STRUCTURE;
    }
}
