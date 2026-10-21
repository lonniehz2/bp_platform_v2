# -*- coding: utf-8 -*-
"""修复：(1) MQ 消息携带 tenantId  (2) 幂等键用原始 validStart"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'

# ============ 1) Producer：捕获 tenantId 并随消息发送 ============
p1 = os.path.join(BASE, r'grant\mq\GrantDispatchProducer.java')
io.open(p1, 'w', encoding='utf-8').write('''package com.yundao.bp.grant.mq;

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
''')
print('  ~ GrantDispatchProducer（携带 tenantId）')

# ============ 2) Consumer：解析并设置租户上下文 ============
p2 = os.path.join(BASE, r'grant\mq\GrantDispatchConsumer.java')
io.open(p2, 'w', encoding='utf-8').write('''package com.yundao.bp.grant.mq;

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
''')
print('  ~ GrantDispatchConsumer（设置/清理租户上下文）')

# ============ 3) 幂等键用原始 validStart，不用解析后的 now() ============
p3 = os.path.join(BASE, r'grant\service\impl\GrantServiceImpl.java')
s = io.open(p3, encoding='utf-8').read()

old = '''        // ---- 2) 幂等：同人+同空间+同层级+同有效期 只建一次 ----
        String idemKey = idempotentKey(cmd.personId(), cmd.spaceId(), cmd.grantLevel(), start, end);'''
new = '''        // ---- 2) 幂等：同人+同空间+同层级+同有效期 只建一次 ----
        // ⚠️ 必须用 cmd 里"原始"的 validStart，不能用上面解析出的 start（=now()）
        //    否则每次申请 now() 都不同，幂等键永远不命中
        String idemKey = idempotentKey(cmd.personId(), cmd.spaceId(), cmd.grantLevel(),
                cmd.validStart(), end);'''
assert old in s, 'idem anchor missing'
s = s.replace(old, new, 1)

# idempotentKey 注释补充
s = s.replace(
    '    /** 幂等键：sha1(personId|spaceId|level|validStart|validEnd)。 */',
    '''    /**
     * 幂等键：{@code sha1(personId|spaceId|level|validStart|validEnd)}。
     *
     * <p>⚠️ {@code validStart} 必须传<b>请求原始值</b>（可为 null），
     * 不能传"解析后的 now()"，否则每次调用键都不同，幂等失效。
     */''', 1)

io.open(p3, 'w', encoding='utf-8').write(s)
print('  ~ GrantServiceImpl（幂等键改用原始 validStart）')
