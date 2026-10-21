package com.yundao.bp.open.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.open.entity.OpenWebhook;
import com.yundao.bp.open.entity.OpenWebhookLog;
import java.util.Map;

/**
 * Webhook 推送服务。
 */
public interface WebhookService {

    OpenWebhook subscribe(String hookName, String callbackUrl, String eventTypes,
                          Integer retryTimes, Integer timeoutMs);

    java.util.List<OpenWebhook> list();

    OpenWebhook setStatus(Long id, String status);

    /**
     * 发布业务事件：找到订阅该事件的所有 Webhook 并逐个推送。
     *
     * <p>推送失败<b>不影响主业务</b>，失败记录留待重试。
     *
     * @return 成功推送条数
     */
    int publish(String eventType, Map<String, Object> payload);

    /** 重试失败推送。 */
    int retryFailed(int limit);

    PageResult<OpenWebhookLog> pageLogs(long pageNum, long pageSize, Long hookId,
                                        String pushStatus);
}
