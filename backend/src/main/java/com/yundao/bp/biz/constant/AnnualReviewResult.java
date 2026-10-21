package com.yundao.bp.biz.constant;

/**
 * 年审（复核）结果（对应 {@code bp_biz_annual_review.review_result}）。
 *
 * <p>与审核结果 {@link ReviewResult} 区分：本枚举表达"保障资格"的复核结论。
 */
public enum AnnualReviewResult {

    KEEP("保留资格"),
    ADJUST("调整（租金/房源）"),
    EXIT("退出"),
    PENDING("待定");

    private final String label;

    AnnualReviewResult(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 是否需要后续处置（调整或退出）。 */
    public boolean needsAction() {
        return this == ADJUST || this == EXIT;
    }
}
