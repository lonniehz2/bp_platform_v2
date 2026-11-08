package com.yundao.bp.property.service;

/** 电子发票开票网关。 */
public interface InvoiceGateway {

    IssueResult issue(IssueRequest request);

    record IssueRequest(Long invoiceId, String receiptNo, String invoiceTitle, String taxNo,
                        String email, java.math.BigDecimal amount) {
    }

    record IssueResult(boolean success, String invoiceNo, String invoiceUrl, String error) {
        public static IssueResult simulated(long invoiceId) {
            return new IssueResult(true, "FP" + invoiceId, null, null);
        }
    }
}
