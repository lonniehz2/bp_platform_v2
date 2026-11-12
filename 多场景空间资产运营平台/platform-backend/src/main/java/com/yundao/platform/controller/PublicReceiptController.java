package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.ReceiptDocumentService;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/public/receipts")
public class PublicReceiptController {

    private final ReceiptDocumentService service;

    public PublicReceiptController(ReceiptDocumentService service) {
        this.service = service;
    }

    @GetMapping("/verify/{token}")
    public R<Map<String, Object>> verify(@PathVariable String token) {
        return R.ok(service.verify(token));
    }
}
