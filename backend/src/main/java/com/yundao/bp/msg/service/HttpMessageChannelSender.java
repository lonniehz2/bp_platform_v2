package com.yundao.bp.msg.service;

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

/**
 * 可配置短信/微信通道适配器。
 *
 * <p>配置 webhook 后，POST JSON 到服务商网关；未配置时保持模拟投递，
 * 便于本地开发和先跑通业务。网关返回 2xx 视为成功。
 */
@Component
public class HttpMessageChannelSender implements MessageChannelSender {

    private static final Logger log = LoggerFactory.getLogger(HttpMessageChannelSender.class);

    private final ObjectMapper objectMapper;
    private final String smsWebhook;
    private final String wechatWebhook;
    private final HttpClient httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(5)).build();

    public HttpMessageChannelSender(ObjectMapper objectMapper,
            @Value("${bp.msg.sms-webhook:}") String smsWebhook,
            @Value("${bp.msg.wechat-webhook:}") String wechatWebhook) {
        this.objectMapper = objectMapper;
        this.smsWebhook = smsWebhook;
        this.wechatWebhook = wechatWebhook;
    }

    @Override
    public SendResult send(String channel, String receiverAddr, String title, String content) {
        String webhook = "SMS".equalsIgnoreCase(channel) ? smsWebhook
                : "WECHAT".equalsIgnoreCase(channel) ? wechatWebhook : "";
        if (webhook == null || webhook.isBlank()) {
            return new SendResult(true, null, null);
        }
        try {
            Map<String, Object> payload = new LinkedHashMap<>();
            payload.put("channel", channel);
            payload.put("to", receiverAddr);
            payload.put("title", title);
            payload.put("content", content);
            HttpRequest request = HttpRequest.newBuilder(URI.create(webhook))
                    .timeout(Duration.ofSeconds(8))
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(
                            objectMapper.writeValueAsString(payload)))
                    .build();
            HttpResponse<String> response = httpClient.send(request,
                    HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() >= 200 && response.statusCode() < 300) {
                String thirdId = response.headers().firstValue("X-Message-Id").orElse(null);
                return new SendResult(true, thirdId, null);
            }
            return new SendResult(false, null, "通道返回 " + response.statusCode());
        } catch (Exception e) {
            log.warn("消息通道发送失败：{} → {}：{}", channel, receiverAddr, e.getMessage());
            return new SendResult(false, null, e.getMessage());
        }
    }
}
