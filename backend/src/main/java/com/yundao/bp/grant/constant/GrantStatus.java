package com.yundao.bp.grant.constant;

import java.util.Map;
import java.util.Set;

/**
 * 权益状态机（对应 {@code bp_grant_entitlement.grant_status}）。
 *
 * <pre>
 *   PENDING ──生效时间到──> EFFECTIVE ──到期──> EXPIRED
 *      │                       │
 *      │                       ├──欠费/违规──> FROZEN ──解除──> EFFECTIVE
 *      │                       └──撤销/退租──> REVOKED（终态）
 *      └──撤销──> REVOKED（终态）
 * </pre>
 */
public enum GrantStatus {

    PENDING("待生效"),
    EFFECTIVE("已生效"),
    EXPIRED("已到期"),
    FROZEN("已冻结"),
    REVOKED("已撤销");

    private final String label;

    GrantStatus(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 允许的迁移。REVOKED / EXPIRED 为终态。 */
    public static Set<GrantStatus> nextOf(GrantStatus from) {
        return switch (from) {
            case PENDING -> Set.of(EFFECTIVE, REVOKED);
            case EFFECTIVE -> Set.of(EXPIRED, FROZEN, REVOKED);
            case FROZEN -> Set.of(EFFECTIVE, REVOKED);
            case EXPIRED, REVOKED -> Set.of();
        };
    }

    /** 是否终态（不可再变更）。 */
    public boolean isTerminal() {
        return this == REVOKED || this == EXPIRED;
    }

    /** 是否占用配额/算有效权益。 */
    public boolean isActive() {
        return this == EFFECTIVE;
    }

    public static Map<String, String> labels() {
        return java.util.Arrays.stream(values())
                .collect(java.util.stream.Collectors.toMap(Enum::name, GrantStatus::label));
    }
}
