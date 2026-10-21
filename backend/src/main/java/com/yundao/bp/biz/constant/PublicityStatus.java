package com.yundao.bp.biz.constant;

import java.util.Set;

/**
 * 公示状态（对应 {@code bp_biz_publicity.publicity_status}）。
 *
 * <pre>
 *   DRAFT 草稿 → PUBLISHED 已发布 → CLOSED 已结束（终态）
 * </pre>
 *
 * <p>⭐ <b>合规要求（决策 D23）</b>：配租结果必须公示，
 * 且公示期不少于 {@code 7} 个自然日；配租公示<b>未结束不得签约</b>。
 */
public enum PublicityStatus {

    DRAFT("草稿", false),
    PUBLISHED("已发布", false),
    CLOSED("已结束", true);

    private final String label;
    private final boolean terminal;

    PublicityStatus(String label, boolean terminal) {
        this.label = label;
        this.terminal = terminal;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return terminal;
    }

    public static Set<PublicityStatus> nextOf(PublicityStatus from) {
        return switch (from) {
            case DRAFT -> Set.of(PUBLISHED);
            case PUBLISHED -> Set.of(CLOSED);
            case CLOSED -> Set.of();
        };
    }
}
