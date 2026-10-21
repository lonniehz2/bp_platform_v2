package com.yundao.bp.ops.constant;

/**
 * 人房匹配结果（对应 {@code bp_ops_house_visit.match_result}）。
 */
public enum MatchResult {

    MATCH("一致"),
    MISMATCH("不一致"),
    UNKNOWN("无法确认");

    private final String label;

    MatchResult(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }
}
