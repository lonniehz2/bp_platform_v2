package com.yundao.bp.grant.mq;

import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
import com.yundao.bp.grant.service.GrantService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Component;

/**
 * 授权下发消费者。
 *
 * <p><b>为什么这里要手工设置 TenantContext</b>：
 * MQ 消费线程不经过 {@code TenantFilter}，没有租户上下文；
 * 而 MyBatis 租户插件强制要求上下文（防跨租户越权），
 * 所以消息里带了 {@code tenantId}，消费时设置、结束后清理。
 *
 * <p>失败不抛异常（避免 MQ 无限重投），任务置为可重试状态，
 * 由 {@code GrantRetryJob} 按次数上限兜底。
 */
@Component
public class GrantDispatchConsumer {

    private static final Logger log = LoggerFactory.getLogger(GrantDispatchConsumer.class);
    private static final String SEP = "|";

    private final GrantService grantService;

    public GrantDispatchConsumer(GrantService grantService) {
        this.grantService = grantService;
    }

    @RabbitListener(queues = GrantMqConfig.QUEUE_DISPATCH)
    public void onMessage(String payload) {
        if (payload == null || payload.isBlank()) {
            log.warn("空授权任务消息，忽略");
            return;
        }
        String tenantId;
        Long taskId;
        int idx = payload.indexOf(SEP);
        try {
            if (idx > 0) {
                tenantId = payload.substring(0, idx);
                taskId = Long.valueOf(payload.substring(idx + 1).trim());
            } else {
                // 兼容旧格式（只有 taskId）—— 无法确定租户，只能告警丢弃
                log.warn("授权任务消息缺少 tenantId，丢弃: {}", payload);
                return;
            }
        } catch (Exception e) {
            log.warn("非法授权任务消息: {}", payload);
            return;
        }

        try {
            TenantContext.set(TenantInfo.of(tenantId, null));
            log.debug("消费授权任务 tenantId={} taskId={}", tenantId, taskId);
            grantService.dispatch(taskId);
        } catch (Exception e) {
            log.error("授权任务下发异常 tenantId={} taskId={}", tenantId, taskId, e);
        } finally {
            // ★ 必须清理：线程池复用会导致串租户
            TenantContext.clear();
        }
    }
}
