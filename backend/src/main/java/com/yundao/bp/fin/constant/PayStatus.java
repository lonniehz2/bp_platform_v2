package com.yundao.bp.fin.constant;

/**
 * 收款单状态（对应 {@code bp_fin_payment.pay_status}）。
 *
 * <p>只有 {@code SUCCESS} 的收款单才能用于核销账单。
 */
public enum PayStatus {

    PENDING("待支付"),
    SUCCESS("成功"),
    FAILED("失败"),
    REFUNDED("已退款");

    private final String label;

    PayStatus(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    public boolean isSuccess() {
        return this == SUCCESS;
    }
}
