package com.yundao.bp.grant.mq;

import org.springframework.amqp.core.Binding;
import org.springframework.amqp.core.BindingBuilder;
import org.springframework.amqp.core.DirectExchange;
import org.springframework.amqp.core.Queue;
import org.springframework.amqp.core.QueueBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * 授权下发的 RabbitMQ 拓扑。
 *
 * <pre>
 *   exchange: bp.grant.exchange (direct, durable)
 *      ├─ routingKey grant.dispatch → queue bp.grant.dispatch（含 DLX）
 *      └─ routingKey grant.retry    → queue bp.grant.dispatch
 *   queue bp.grant.dispatch.dlq 承接失败消息
 * </pre>
 */
@Configuration
public class GrantMqConfig {

    public static final String EXCHANGE = "bp.grant.exchange";
    public static final String QUEUE_DISPATCH = "bp.grant.dispatch";
    public static final String QUEUE_DLQ = "bp.grant.dispatch.dlq";
    public static final String RK_DISPATCH = "grant.dispatch";
    public static final String RK_RETRY = "grant.retry";

    @Bean
    public DirectExchange grantExchange() {
        return new DirectExchange(EXCHANGE, true, false);
    }

    @Bean
    public Queue grantDispatchQueue() {
        return QueueBuilder.durable(QUEUE_DISPATCH)
                .withArgument("x-dead-letter-exchange", "")
                .withArgument("x-dead-letter-routing-key", QUEUE_DLQ)
                .build();
    }

    @Bean
    public Queue grantDlq() {
        return QueueBuilder.durable(QUEUE_DLQ).build();
    }

    @Bean
    public Binding grantDispatchBinding() {
        return BindingBuilder.bind(grantDispatchQueue()).to(grantExchange()).with(RK_DISPATCH);
    }

    @Bean
    public Binding grantRetryBinding() {
        return BindingBuilder.bind(grantDispatchQueue()).to(grantExchange()).with(RK_RETRY);
    }
}
