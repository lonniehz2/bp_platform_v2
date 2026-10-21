package com.yundao.bp.fin.constant;

/**
 * 流水校验状态（对应 {@code bp_fin_cash_flow.verify_status}）。
 *
 * <p>业务数据变更后（如账单减免、退款冲销），流水金额可能与业务账面不一致，
 * 校验用于标记这类差异。
 */
public enum VerifyStatus {

    UNVERIFIED("未校验"),
    VERIFIED("已校验"),
    ABNORMAL("异常");

    private final String label;

    VerifyStatus(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }
}
