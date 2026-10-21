package com.yundao.bp.biz.constant;

/**
 * 审核阶段（对应 {@code bp_biz_review_record.review_stage}）。
 *
 * <p>保障房审核通常是多级/多部门联审：
 * 受理初审 → 形式审查 → 多部门联审（不动产/民政/社保等）→ 终审。
 */
public enum ReviewStage {

    ACCEPT("受理初审"),
    FORM("形式审查"),
    JOINT("多部门联审"),
    FINAL("终审");

    private final String label;

    ReviewStage(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 按顺序取下一阶段；已是终审则返回 null。 */
    public ReviewStage next() {
        ReviewStage[] all = values();
        int i = ordinal() + 1;
        return i < all.length ? all[i] : null;
    }

    /** 是否最后一阶段（通过即 APPROVED）。 */
    public boolean isLast() {
        return next() == null;
    }
}
