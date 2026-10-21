package com.yundao.bp.biz.constant;

/**
 * 审核结果（对应 {@code bp_biz_review_record.review_result}）。
 *
 * <p>注意：年审（复核）结果用的是另一个枚举
 * {@link AnnualReviewResult}（KEEP/ADJUST/EXIT/PENDING），两者不可混用。
 */
public enum ReviewResult {

    PASS("通过"),
    REJECT("不通过"),
    SUPPLEMENT("需补件");

    private final String label;

    ReviewResult(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 是否通过。 */
    public boolean isPass() {
        return this == PASS;
    }
}
