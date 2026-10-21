package com.yundao.bp.biz.constant;

/**
 * 申诉/异议的业务类型（对应 {@code bp_biz_appeal.biz_type}）。
 *
 * <p>决定可申诉的对象：申请审批、审核、年度核查、公示、退出。
 */
public enum AppealBizType {

    APPLICATION("申请"),
    REVIEW("审核"),
    ANNUAL_REVIEW("年度核查"),
    PUBLICITY("公示异议"),
    EXIT("退出");

    private final String label;

    AppealBizType(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }
}
