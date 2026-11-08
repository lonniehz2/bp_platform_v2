package com.yundao.bp.property.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.property.service.PropertyBillingService;
import com.yundao.bp.property.service.PropertyReceiptPdfService;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** 物业收费闭环：收费项目、账单、收款、收据。 */
@RestController
@RequestMapping("/api/v1/property")
public class PropertyBillingController {

    private final PropertyBillingService service;
    private final PropertyReceiptPdfService receiptPdfService;

    public PropertyBillingController(PropertyBillingService service,
                                     PropertyReceiptPdfService receiptPdfService) {
        this.service = service;
        this.receiptPdfService = receiptPdfService;
    }

    @com.yundao.bp.iam.security.RequirePerm("property:bill:view")
    @GetMapping("/fee-items")
    public R<List<Map<String, Object>>> feeItems(@RequestParam Long projectId) {
        return R.ok(service.feeItems(projectId));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:bill:manage")
    @PostMapping("/fee-items")
    public R<Map<String, Object>> createFeeItem(@RequestParam Long projectId,
            @RequestBody PropertyBillingService.FeeItemCmd cmd) {
        return R.ok(service.createFeeItem(projectId, cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:bill:manage")
    @PostMapping("/bills/generate")
    public R<Map<String, Object>> generate(@RequestBody PropertyBillingService.GenerateCmd cmd) {
        return R.ok(service.generateBills(cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:bill:view")
    @GetMapping("/bills")
    public R<Map<String, Object>> bills(@RequestParam Long projectId,
            @RequestParam(defaultValue = "1") int pageNum,
            @RequestParam(defaultValue = "20") int pageSize,
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String keyword) {
        return R.ok(service.pageBills(projectId, pageNum, pageSize, status, keyword));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:payment:create")
    @PostMapping("/payments")
    public R<Map<String, Object>> pay(@RequestBody PropertyBillingService.PayCmd cmd) {
        return R.ok(service.pay(cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("property:receipt:view")
    @GetMapping("/receipts/{id}/pdf")
    public org.springframework.http.ResponseEntity<byte[]> receiptPdf(
            @org.springframework.web.bind.annotation.PathVariable Long id) {
        byte[] pdf = receiptPdfService.render(id);
        return org.springframework.http.ResponseEntity.ok()
                .header("Content-Type", "application/pdf")
                .header("Content-Disposition", "inline; filename=receipt-" + id + ".pdf")
                .body(pdf);
    }

    @com.yundao.bp.iam.security.RequirePerm("property:receipt:view")
    @GetMapping("/receipts")
    public R<List<Map<String, Object>>> receipts(@RequestParam Long projectId) {
        return R.ok(service.receipts(projectId));
    }
}
