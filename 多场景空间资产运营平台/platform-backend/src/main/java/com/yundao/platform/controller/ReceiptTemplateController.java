package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.ReceiptTemplateService;
import com.yundao.platform.service.ReceiptDocumentService;
import com.yundao.platform.service.ReceiptPdfService;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/platform/receipt-templates")
public class ReceiptTemplateController {
    private final ReceiptTemplateService service;
    private final com.yundao.platform.service.PermissionService permissions;
    private final ReceiptDocumentService documents;
    private final ReceiptPdfService pdf;

    public ReceiptTemplateController(ReceiptTemplateService service, com.yundao.platform.service.PermissionService permissions,
                                     ReceiptDocumentService documents, ReceiptPdfService pdf) {
        this.service = service;
        this.permissions = permissions;
        this.documents = documents;
        this.pdf = pdf;
    }

    @GetMapping
    public R<List<Map<String, Object>>> list() { permissions.require("billing:view"); return R.ok(service.list()); }

    @PostMapping
    public R<Map<String, Object>> create(@RequestBody ReceiptTemplateService.Cmd cmd) { permissions.require("billing:adjust"); return R.ok(service.create(cmd.templateName(), cmd.configJson())); }

    @PostMapping("/{id}")
    public R<Map<String, Object>> update(@PathVariable long id, @RequestBody ReceiptTemplateService.Cmd cmd) { permissions.require("billing:adjust"); return R.ok(service.update(id, cmd.templateName(), cmd.configJson())); }

    @GetMapping("/{id}/history")
    public R<List<Map<String, Object>>> history(@PathVariable long id) { permissions.require("billing:view"); return R.ok(service.history(id)); }

    @GetMapping(value = "/{id}/preview.pdf", produces = MediaType.APPLICATION_PDF_VALUE)
    public ResponseEntity<byte[]> preview(@PathVariable long id) {
        permissions.require("billing:view");
        Map<String, Object> sample = new LinkedHashMap<>();
        sample.put("receiptNo", "PREVIEW-001");
        sample.put("paymentNo", "PAY-PREVIEW-001");
        sample.put("amount", "100.00");
        sample.put("paymentMethod", "CASH");
        sample.put("issuedTime", "2026-11-12 12:00:00");
        sample.put("receiptStatus", "VALID");
        byte[] bytes = pdf.render(sample, documents.config(id), "https://example.com/verify/PREVIEW", "PREVIEW1");
        return ResponseEntity.ok().header("Content-Disposition", "inline; filename=\"receipt-preview.pdf\"").contentType(MediaType.APPLICATION_PDF).body(bytes);
    }

    @PostMapping("/{id}/publish")
    public R<Map<String, Object>> publish(@PathVariable long id) { permissions.require("billing:adjust"); return R.ok(service.publish(id)); }
}
