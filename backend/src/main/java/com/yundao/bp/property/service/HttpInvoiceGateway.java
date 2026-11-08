package com.yundao.bp.property.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/** 可配置税控/电子发票网关。未配置时模拟开票。 */
@Component
public class HttpInvoiceGateway implements InvoiceGateway {

    private static final Logger log = LoggerFactory.getLogger(HttpInvoiceGateway.class);

    private final ObjectMapper objectMapper;
    private final String webhook;
    private final HttpClient httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(5)).build();

    public HttpInvoiceGateway(ObjectMapper objectMapper,
            @Value("${bp.property.invoice-webhook:}") String webhook) {
        this.objectMapper = objectMapper;
        this.webhook = webhook;
    }

    @Override
    public IssueResult issue(IssueRequest request) {
        if (webhook == null || webhook.isBlank()) {
            return IssueResult.simulated(request.invoiceId());
        }
        try {
            Map<String, Object> payload = new LinkedHashMap<>();
            payload.put("invoiceId", request.invoiceId());
            payload.put("receiptNo", request.receiptNo());
            payload.put("invoiceTitle", request.invoiceTitle());
            payload.put("taxNo", request.taxNo());
            payload.put("email", request.email());
            payload.put("amount", request.amount());
            HttpRequest httpRequest = HttpRequest.newBuilder(URI.create(webhook))
                    .timeout(Duration.ofSeconds(10))
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(
                            objectMapper.writeValueAsString(payload)))
                    .build();
            HttpResponse<String> response = httpClient.send(httpRequest,
                    HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() < 200 || response.statusCode() >= 300) {
                return new IssueResult(false, null, null, "开票网关返回 " + response.statusCode());
            }
            String invoiceNo = "FP" + request.invoiceId();
            String invoiceUrl = null;
            try {
                JsonNode json = objectMapper.readTree(response.body());
                if (json.hasNonNull("invoiceNo")) invoiceNo = json.get("invoiceNo").asText();
                if (json.hasNonNull("invoiceUrl")) invoiceUrl = json.get("invoiceUrl").asText();
            } catch (Exception ignored) {
                // 网关可能返回非 JSON，保留默认发票号
            }
            return new IssueResult(true, invoiceNo, invoiceUrl, null);
        } catch (Exception e) {
            log.warn("电子发票开票失败：invoiceId={}：{}", request.invoiceId(), e.getMessage());
            return new IssueResult(false, null, null, e.getMessage());
        }
    }
}
