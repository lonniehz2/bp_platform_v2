package com.yundao.bp.fin.constant;

/**
 * 催缴方式（对应 {@code bp_fin_dunning_record.dunning_type}）。
 */
public enum DunningType {

    SMS("短信"),
    WECHAT("微信"),
    PHONE("电话"),
    VISIT("上门"),
    NOTICE("通知书"),
    PLATFORM("平台消息");

    private final String label;

    DunningType(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 是否需要留证（照片/通话记录）。 */
    public boolean needsEvidence() {
        return this == VISIT || this == PHONE;
    }
}
