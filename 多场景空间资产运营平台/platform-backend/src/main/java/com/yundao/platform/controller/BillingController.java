package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.BillingService;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/platform/billing")
public class BillingController {

    private final BillingService service;
    private final com.yundao.platform.service.PermissionService permissions;
    private final com.yundao.platform.service.ReceiptPdfService receiptPdfService;
    private final com.yundao.platform.service.ReceiptDocumentService receiptDocumentService;
    @Value("${bp.receipt.verify-base-url:http://localhost:8091/#/verify/receipt/}")
    private String verifyBaseUrl;

    public BillingController(BillingService service,
                             com.yundao.platform.service.PermissionService permissions,
                             com.yundao.platform.service.ReceiptPdfService receiptPdfService,
                             com.yundao.platform.service.ReceiptDocumentService receiptDocumentService) {
        this.service = service;
        this.permissions = permissions;
        this.receiptPdfService = receiptPdfService;
        this.receiptDocumentService = receiptDocumentService;
    }

    @GetMapping("/bills")
    public R<List<Map<String, Object>>> bills(@RequestParam long projectId,
                                              @RequestParam(required = false) String status) {
        return R.ok(service.bills(projectId, status));
    }

    @GetMapping("/contracts/{contractId}/bills")
    public R<List<Map<String, Object>>> contractBills(@PathVariable long contractId) {
        return R.ok(service.contractBills(contractId));
    }

    @PostMapping("/contracts/{contractId}/pay")
    public R<Map<String, Object>> payContract(@PathVariable long contractId,
                                              @RequestBody BillingService.ContractPayCmd cmd) {
        permissions.require("billing:pay");
        return R.ok(service.payContract(contractId, cmd));
    }

    @PostMapping("/contracts/{contractId}/opening-bills")
    public R<Map<String, Object>> openingBill(@PathVariable long contractId,
                                              @RequestBody BillingService.BillCmd cmd) {
        permissions.require("billing:opening");
        return R.ok(service.createOpeningBill(contractId, cmd));
    }

    @PostMapping("/bills/{billId}/pay")
    public R<Map<String, Object>> pay(@PathVariable long billId,
                                      @RequestBody BillingService.PaymentCmd cmd) {
        permissions.require("billing:pay");
        return R.ok(service.pay(billId, cmd));
    }

    @PostMapping("/bills/{billId}/discard")
    public R<Map<String, Object>> discard(@PathVariable long billId) {
        permissions.require("billing:discard");
        return R.ok(service.discardBill(billId));
    }

    @PostMapping("/bills/{billId}/close")
    public R<Map<String, Object>> close(@PathVariable long billId) {
        permissions.require("billing:close");
        return R.ok(service.closeBill(billId));
    }

    @PostMapping("/bills/{billId}/adjust")
    public R<Map<String, Object>> adjust(@PathVariable long billId,
                                         @RequestBody BillingService.AdjustCmd cmd) {
        permissions.require("billing:adjust");
        return R.ok(service.adjust(billId, cmd));
    }

    @GetMapping("/payments/{paymentId}/allocations")
    public R<List<Map<String, Object>>> paymentAllocations(@PathVariable long paymentId) {
        return R.ok(service.paymentAllocations(paymentId));
    }

    @PostMapping("/payments/{paymentId}/refund")
    public R<Map<String, Object>> refund(@PathVariable long paymentId,
                                         @RequestBody BillingService.RefundCmd cmd) {
        permissions.require("billing:refund");
        return R.ok(service.refund(paymentId, cmd));
    }

    @GetMapping("/payments")
    public R<List<Map<String, Object>>> payments(@RequestParam long projectId) {
        return R.ok(service.payments(projectId));
    }

    @GetMapping("/payments/{paymentId}/receipt")
    public R<Map<String, Object>> receipt(@PathVariable long paymentId) {
        return R.ok(service.receipt(paymentId));
    }

    @PostMapping("/payments/{paymentId}/receipt/void")
    public R<Map<String, Object>> voidReceipt(@PathVariable long paymentId) {
        permissions.require("billing:adjust");
        Map<String, Object> receipt = service.receipt(paymentId);
        receiptDocumentService.markStatus(Long.parseLong(String.valueOf(receipt.get("id"))), "VOID");
        return R.ok(Map.of("paymentId", paymentId, "status", "VOID"));
    }

    @GetMapping(value = "/payments/{paymentId}/receipt/pdf", produces = MediaType.APPLICATION_PDF_VALUE)
    public ResponseEntity<byte[]> receiptPdf(@PathVariable long paymentId,
                                             @RequestParam(defaultValue = "false") boolean inline) {
        permissions.require("billing:view");
        Map<String, Object> receipt = service.receipt(paymentId);
        long receiptId = Long.parseLong(String.valueOf(receipt.get("id")));
        long projectId = Long.parseLong(String.valueOf(receipt.get("projectId")));
        Map<String, Object> doc = receiptDocumentService.getOrCreate(receiptId, projectId);
        Map<String, Object> config = receiptDocumentService.config(Long.parseLong(String.valueOf(doc.get("templateId"))));
        String url = verifyBaseUrl + doc.get("token");
        byte[] pdf = receiptPdfService.render(receipt, config, url, String.valueOf(doc.get("code")));
        receiptDocumentService.savePdfHash(receiptId, receiptPdfService.sha256(pdf));
        return ResponseEntity.ok()
                .header("Content-Disposition", (inline ? "inline" : "attachment") + "; filename=\"receipt-" + paymentId + ".pdf\"")
                .contentType(MediaType.APPLICATION_PDF)
                .body(pdf);
    }
}
