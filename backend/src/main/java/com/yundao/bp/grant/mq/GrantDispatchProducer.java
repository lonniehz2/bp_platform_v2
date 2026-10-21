package com.yundao.bp.grant.mq;

import com.yundao.bp.common.tenant.TenantContext;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.stereotype.Component;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;

/**
 * 授权任务投递。
 *
 * <p><b>两个关键设计</b>：
 * <ol>
 *   <li><b>事务提交后投递</b>：否则消费者可能在提交前读到任务（读不到）或读到被回滚的数据。</li>
 *   <li><b>消息必须携带 tenantId</b>：MQ 消费线程没有 TenantContext，
 *       而 MyBatis 租户插件会强制要求它（fail-on-missing），
 *       否则消费者一查库就抛 {@code BP20004 租户上下文缺失}。</li>
 * </ol>
 *
 * <p>消息格式：{@code tenantId|taskId}
 */
@Component
public class GrantDispatchProducer {

    private static final Logger log = LoggerFactory.getLogger(GrantDispatchProducer.class);
    private static final String SEP = "|";

    private final RabbitTemplate rabbit;

    public GrantDispatchProducer(RabbitTemplate rabbit) {
        this.rabbit = rabbit;
    }

    /** 投递下发消息（事务内调用则延迟到提交后）。 */
    public void publishDispatch(Long taskId) {
        publish(GrantMqConfig.RK_DISPATCH, taskId);
    }

    public void publishRetry(Long taskId) {
        publish(GrantMqConfig.RK_RETRY, taskId);
    }

    private void publish(String routingKey, Long taskId) {
        // ★ 必须在当前线程（有上下文）时捕获租户，不能放到 afterCommit 里再取
        final String tenantId = TenantContext.tenantId();
        final String payload = tenantId + SEP + taskId;

        if (TransactionSynchronizationManager.isSynchronizationActive()) {
            TransactionSynchronizationManager.registerSynchronization(
                    new TransactionSynchronization() {
                        @Override
                        public void afterCommit() {
                            doPublish(routingKey, payload);
                        }
                    });
        } else {
            doPublish(routingKey, payload);
        }
    }

    private void doPublish(String routingKey, String payload) {
        try {
            rabbit.convertAndSend(GrantMqConfig.EXCHANGE, routingKey, payload);
            log.debug("授权任务已投递 payload={} rk={}", payload, routingKey);
        } catch (Exception e) {
            // MQ 不可用不影响主流程：任务保持 PENDING，由重试任务兜底
            log.warn("授权任务投递失败（将由重试任务兜底） payload={} err={}", payload, e.getMessage());
        }
    }
}
