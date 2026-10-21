package com.yundao.bp.biz.constant;

import java.util.Set;

/**
 * 合同状态机（对应 {@code bp_biz_contract.contract_status}）。
 *
 * <pre>
 *   DRAFT 草稿 ──提交签约──> PENDING_SIGN 待签约 ──发起──> SIGNING 签约中
 *                                                          │
 *                                                    签署完成
 *                                                          ↓
 *   RENEWING 续签中 ←──续签── EFFECTIVE 履约中 ──到期──> EXPIRED 已到期
 *                                  │
 *                             ──退租/终止──> TERMINATED 已终止
 *   DRAFT/PENDING_SIGN ──作废──> CANCELLED
 * </pre>
 *
 * <p><b>业务要害</b>：{@code EFFECTIVE} 时会按 {@code auto_grant} 自动下发权限，
 * {@code TERMINATED/EXPIRED} 时按 {@code auto_expire} 自动撤权 —— 这是
 * "合同驱动授权"的关键联动点。
 */
public enum ContractStatus {

    DRAFT("草稿", false),
    PENDING_SIGN("待签约", false),
    SIGNING("签约中", false),
    EFFECTIVE("履约中", false),
    RENEWING("续签中", false),
    EXPIRED("已到期", true),
    TERMINATED("已终止", true),
    CANCELLED("已作废", true);

    private final String label;
    private final boolean terminal;

    ContractStatus(String label, boolean terminal) {
        this.label = label;
        this.terminal = terminal;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return terminal;
    }

    /** 是否是"占房"状态（房源应显示已租）。 */
    public boolean isOccupying() {
        return this == EFFECTIVE || this == RENEWING;
    }

    public static Set<ContractStatus> nextOf(ContractStatus from) {
        return switch (from) {
            case DRAFT -> Set.of(PENDING_SIGN, CANCELLED);
            case PENDING_SIGN -> Set.of(SIGNING, CANCELLED);
            case SIGNING -> Set.of(EFFECTIVE, CANCELLED);
            case EFFECTIVE -> Set.of(RENEWING, EXPIRED, TERMINATED);
            case RENEWING -> Set.of(EFFECTIVE, TERMINATED);
            case EXPIRED, TERMINATED, CANCELLED -> Set.of();
        };
    }
}
