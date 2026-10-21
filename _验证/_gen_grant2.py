# -*- coding: utf-8 -*-
"""生成 grant 授权编排模块（第 2 部分：IoT 客户端/服务/MQ/控制器/重试）"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

# ==================== IoT 授权客户端抽象 ====================
FILES['grant/iot/IotGrantRequest.java'] = '''package com.yundao.bp.grant.iot;

import java.time.LocalDateTime;
import java.util.List;

/**
 * IoT 授权请求（与具体平台无关的中间模型）。
 *
 * @param personId   本地人员 ID
 * @param iotOwnerId IoT 侧人员主键（若已映射）
 * @param account    IoT 侧账号（通常手机号）
 * @param lockIds    目标门锁 ID 列表
 * @param validStart 生效时间
 * @param validEnd   失效时间（null=永久）
 * @param channelType 介质类型（null=仅 App 权限）
 */
public record IotGrantRequest(
        Long personId,
        String iotOwnerId,
        String account,
        List<String> lockIds,
        LocalDateTime validStart,
        LocalDateTime validEnd,
        String channelType,
        String channelModuleType
) {
}
'''

FILES['grant/iot/IotGrantResult.java'] = '''package com.yundao.bp.grant.iot;

import java.util.List;

/**
 * IoT 授权结果。
 *
 * @param iotTaskId 平台异步任务 ID（非空表示需轮询 {@code syncTask/result/list}）
 * @param success   请求是否被接受
 * @param message   平台消息
 * @param devices   逐设备结果（同步返回时可用）
 */
public record IotGrantResult(
        String iotTaskId,
        boolean success,
        String message,
        List<DeviceResult> devices
) {
    public record DeviceResult(String lockId, boolean success, String errorCode,
                               String errorMsg, Integer durationMs) {
    }

    public static IotGrantResult ok(String iotTaskId, String message, List<DeviceResult> devices) {
        return new IotGrantResult(iotTaskId, true, message, devices);
    }

    public static IotGrantResult fail(String message) {
        return new IotGrantResult(null, false, message, List.of());
    }
}
'''

FILES['grant/iot/IotGrantClient.java'] = '''package com.yundao.bp.grant.iot;

/**
 * IoT 授权客户端抽象。
 *
 * <p>为什么抽象：现网 IoT 的授权接口参数尚未与我们联调确认
 * （见 {@code _验证/IoT对接规范-定稿.md} §6），
 * 因此把"下发"抽成接口，编排逻辑可以先用 {@link MockIotGrantClient} 完整验证，
 * 联调确认后只替换实现，编排代码不用动。
 *
 * <p>可用配置 {@code bp.grant.iot-mode=mock|real} 切换。
 */
public interface IotGrantClient {

    /** 下发授权。 */
    IotGrantResult grant(IotGrantRequest req);

    /** 撤销授权。 */
    IotGrantResult revoke(IotGrantRequest req);

    /** 轮询异步任务结果（{@code iotTaskId} 非空时使用）。 */
    IotGrantResult queryTaskResult(String iotTaskId);
}
'''

FILES['grant/iot/MockIotGrantClient.java'] = '''package com.yundao.bp.grant.iot;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicLong;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * 模拟 IoT 授权客户端（<b>默认</b>，仅用于编排验证与演示）。
 *
 * <p>⚠️ 它不会真正下发到门锁。启用条件：{@code bp.grant.iot-mode=mock}（默认）。
 * 启动时会打印 WARN 提醒。
 *
 * <p>行为：对每个 lockId 返回成功，模拟 5ms 耗时，用于验证
 * 任务状态机、明细写入、统计与重试。
 */
public class MockIotGrantClient implements IotGrantClient {

    private static final Logger log = LoggerFactory.getLogger(MockIotGrantClient.class);
    private final AtomicLong seq = new AtomicLong(System.currentTimeMillis() % 100000);

    public MockIotGrantClient() {
        log.warn("========================================================");
        log.warn(" IoT 授权使用 MOCK 实现：不会真正下发到门锁！");
        log.warn(" 要对接真实平台，请设置 bp.grant.iot-mode=real");
        log.warn("========================================================");
    }

    @Override
    public IotGrantResult grant(IotGrantRequest req) {
        List<IotGrantResult.DeviceResult> devs = new ArrayList<>();
        for (String lockId : req.lockIds()) {
            devs.add(new IotGrantResult.DeviceResult(lockId, true, null, null, 5));
        }
        String taskId = "MOCK-" + seq.incrementAndGet();
        return IotGrantResult.ok(taskId, "MOCK 授权已受理", devs);
    }

    @Override
    public IotGrantResult revoke(IotGrantRequest req) {
        List<IotGrantResult.DeviceResult> devs = new ArrayList<>();
        for (String lockId : req.lockIds()) {
            devs.add(new IotGrantResult.DeviceResult(lockId, true, null, null, 5));
        }
        return IotGrantResult.ok("MOCK-R-" + seq.incrementAndGet(), "MOCK 撤销已受理", devs);
    }

    @Override
    public IotGrantResult queryTaskResult(String iotTaskId) {
        // 模拟：立刻返回成功，明细由编排层按原请求补齐
        return IotGrantResult.ok(iotTaskId, "MOCK 任务已完成", List.of());
    }
}
'''

FILES['grant/iot/YmdGrantClient.java'] = '''package com.yundao.bp.grant.iot;

import com.fasterxml.jackson.core.type.TypeReference;
import com.yundao.bp.iot.legacy.YmdClient;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * 云门道 IoT 授权客户端（真实实现）。
 *
 * <p>⚠️ <b>状态：骨架，参数待与 IoT 方联调确认</b>。
 * 端点已从接口文档确认存在：
 * <ul>
 *   <li>{@code /ymd/restful/channel/auth/action} —— 人员授权</li>
 *   <li>{@code /ymd/restful/auth/action} —— 通用介质授权（含人脸）</li>
 *   <li>{@code /ymd/restful/auth/delAuthById} —— 删除授权</li>
 *   <li>{@code /ymd/restful/syncTask/result/list} —— 异步任务结果查询</li>
 *   <li>{@code /ymd/restful/user/add} —— 人员添加（授权前置）</li>
 * </ul>
 *
 * <p><b>待确认项</b>（见 {@code _验证/IoT对接规范-定稿.md} §6）：
 * 各接口的具体参数名、门锁标识用 {@code lockId} 还是 {@code mac}、
 * 有效期字段格式、是否按 lockId 逐个下发。
 *
 * <p>因此本实现仅按最可能的参数拼装，<b>未经真实环境验证</b>，
 * 联调时需逐项核对。默认不启用（{@code bp.grant.iot-mode=mock}）。
 */
public class YmdGrantClient implements IotGrantClient {

    private static final Logger log = LoggerFactory.getLogger(YmdGrantClient.class);
    private static final DateTimeFormatter FMT =
            DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    private static final String PATH_PERSON_AUTH = "/ymd/restful/channel/auth/action";
    private static final String PATH_AUTH_ACTION = "/ymd/restful/auth/action";
    private static final String PATH_DEL_AUTH = "/ymd/restful/auth/delAuthById";
    private static final String PATH_TASK_RESULT = "/ymd/restful/syncTask/result/list";

    private final YmdClient client;

    public YmdGrantClient(YmdClient client) {
        this.client = client;
        log.warn("IoT 授权使用真实实现：参数尚未联调确认，请核对后再上线");
    }

    @Override
    public IotGrantResult grant(IotGrantRequest req) {
        try {
            Map<String, String> p = new HashMap<>();
            if (req.iotOwnerId() != null) {
                p.put("ownerId", req.iotOwnerId());
            }
            if (req.account() != null) {
                p.put("account", req.account());
            }
            // TODO 联调确认：门锁列表字段名（lockIds / lockid / macList）
            p.put("lockIds", String.join(",", req.lockIds()));
            if (req.validStart() != null) {
                p.put("validStart", req.validStart().format(FMT));
            }
            if (req.validEnd() != null) {
                p.put("validEnd", req.validEnd().format(FMT));
            }
            if (req.channelType() != null) {
                p.put("channelType", req.channelType());
            }
            if (req.channelModuleType() != null) {
                p.put("channelModuleType", req.channelModuleType());
            }

            String path = req.channelType() == null ? PATH_PERSON_AUTH : PATH_AUTH_ACTION;
            String raw = client.callRaw(path, p);
            // TODO 联调确认：响应结构（iotTaskId 字段名可能是 taskId / data.taskId）
            String taskId = com.yundao.bp.iot.legacy.YmdJsonPublic.extract(raw, "taskId");
            return IotGrantResult.ok(taskId, "已提交", List.of());
        } catch (Exception e) {
            log.warn("IoT 授权下发失败: {}", e.getMessage());
            return IotGrantResult.fail(e.getMessage());
        }
    }

    @Override
    public IotGrantResult revoke(IotGrantRequest req) {
        try {
            Map<String, String> p = new HashMap<>();
            if (req.iotOwnerId() != null) {
                p.put("ownerId", req.iotOwnerId());
            }
            p.put("lockIds", String.join(",", req.lockIds()));
            String raw = client.callRaw(PATH_DEL_AUTH, p);
            return IotGrantResult.ok(null, "撤销已提交: " + brief(raw), List.of());
        } catch (Exception e) {
            return IotGrantResult.fail(e.getMessage());
        }
    }

    @Override
    public IotGrantResult queryTaskResult(String iotTaskId) {
        try {
            Map<String, String> p = new HashMap<>();
            p.put("taskId", iotTaskId);
            String raw = client.callRaw(PATH_TASK_RESULT, p);
            return IotGrantResult.ok(iotTaskId, brief(raw), List.of());
        } catch (Exception e) {
            return IotGrantResult.fail(e.getMessage());
        }
    }

    private static String brief(String s) {
        return s == null ? "" : (s.length() > 200 ? s.substring(0, 200) + "..." : s);
    }
}
'''

# ==================== MQ ====================
FILES['grant/mq/GrantMqConfig.java'] = '''package com.yundao.bp.grant.mq;

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
'''

FILES['grant/mq/GrantDispatchProducer.java'] = '''package com.yundao.bp.grant.mq;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.stereotype.Component;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;

/**
 * 授权任务投递。
 *
 * <p><b>关键：在事务提交后投递</b>。否则消费者可能在事务提交前读到任务（读不到），
 * 或读到后被回滚的数据。
 */
@Component
public class GrantDispatchProducer {

    private static final Logger log = LoggerFactory.getLogger(GrantDispatchProducer.class);

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
        if (TransactionSynchronizationManager.isSynchronizationActive()) {
            TransactionSynchronizationManager.registerSynchronization(
                    new TransactionSynchronization() {
                        @Override
                        public void afterCommit() {
                            doPublish(routingKey, taskId);
                        }
                    });
        } else {
            doPublish(routingKey, taskId);
        }
    }

    private void doPublish(String routingKey, Long taskId) {
        try {
            rabbit.convertAndSend(GrantMqConfig.EXCHANGE, routingKey, String.valueOf(taskId));
            log.debug("授权任务已投递 taskId={} rk={}", taskId, routingKey);
        } catch (Exception e) {
            // MQ 不可用不影响主流程：任务保持 PENDING，由重试任务兜底
            log.warn("授权任务投递失败（将由重试任务兜底） taskId={} err={}", taskId, e.getMessage());
        }
    }
}
'''

FILES['grant/mq/GrantDispatchConsumer.java'] = '''package com.yundao.bp.grant.mq;

import com.yundao.bp.grant.service.GrantService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Component;

/**
 * 授权下发消费者。
 *
 * <p>失败不抛异常（不触发无限重投），而是把任务标为可重试状态，
 * 由 {@code GrantRetryJob} 按次数上限兜底。
 */
@Component
public class GrantDispatchConsumer {

    private static final Logger log = LoggerFactory.getLogger(GrantDispatchConsumer.class);

    private final GrantService grantService;

    public GrantDispatchConsumer(GrantService grantService) {
        this.grantService = grantService;
    }

    @RabbitListener(queues = GrantMqConfig.QUEUE_DISPATCH)
    public void onMessage(String payload) {
        Long taskId = null;
        try {
            taskId = Long.valueOf(payload.trim());
        } catch (Exception e) {
            log.warn("非法授权任务消息: {}", payload);
            return;
        }
        log.debug("消费授权任务 taskId={}", taskId);
        try {
            grantService.dispatch(taskId);
        } catch (Exception e) {
            // 兜底：dispatch 内部已处理状态，这里只记日志，避免 MQ 无限重投
            log.error("授权任务下发异常 taskId={}", taskId, e);
        }
    }
}
'''

# ==================== Service ====================
FILES['grant/service/GrantService.java'] = '''package com.yundao.bp.grant.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.grant.dto.GrantApplyCmd;
import com.yundao.bp.grant.dto.GrantTaskVO;
import com.yundao.bp.grant.dto.GrantVO;

/**
 * 授权编排服务。
 */
public interface GrantService {

    /**
     * 申请授权：创建权益 + 创建下发任务（幂等）+ 投递 MQ。
     *
     * <p>返回时任务通常仍为 {@code PENDING}，真正下发是异步的。
     */
    GrantVO apply(GrantApplyCmd cmd);

    GrantVO get(Long id);

    PageResult<GrantVO> page(long pageNum, long pageSize, Long personId, Long spaceId,
                             String grantStatus);

    GrantTaskVO task(Long taskId);

    /** 撤销授权（同时生成 REVOKE 任务）。 */
    GrantVO revoke(Long id, String reason);

    /** 执行下发（供 MQ 消费者/重试任务调用）；幂等。 */
    void dispatch(Long taskId);
}
'''

FILES['grant/service/impl/GrantServiceImpl.java'] = '''package com.yundao.bp.grant.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.grant.constant.GrantStatus;
import com.yundao.bp.grant.constant.GrantTaskStatus;
import com.yundao.bp.grant.dto.GrantApplyCmd;
import com.yundao.bp.grant.dto.GrantTaskVO;
import com.yundao.bp.grant.dto.GrantVO;
import com.yundao.bp.grant.entity.GrantEntitlement;
import com.yundao.bp.grant.entity.GrantTask;
import com.yundao.bp.grant.entity.GrantTaskDetail;
import com.yundao.bp.grant.iot.IotGrantClient;
import com.yundao.bp.grant.iot.IotGrantRequest;
import com.yundao.bp.grant.iot.IotGrantResult;
import com.yundao.bp.grant.mapper.GrantEntitlementMapper;
import com.yundao.bp.grant.mapper.GrantTaskDetailMapper;
import com.yundao.bp.grant.mapper.GrantTaskMapper;
import com.yundao.bp.grant.mq.GrantDispatchProducer;
import com.yundao.bp.grant.service.GrantService;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 授权编排实现。
 *
 * <p><b>闭环</b>：
 * <pre>
 * apply()  → 权益(EFFECTIVE) + 任务(PENDING) + 投递 MQ
 *             ↓（事务提交后）
 * MQ       → consumer → dispatch()
 *             ↓
 * dispatch()→ 任务(DISPATCHING) → IoT 下发 → 明细逐设备 → 任务(SUCCESS/PARTIAL/FAILED)
 * </pre>
 *
 * <p><b>幂等</b>：{@code idempotent_key = sha1(personId|spaceId|level|validStart|validEnd)}，
 * 库上有唯一索引；重复申请直接返回已有权益，不重复下发。
 */
@Service
public class GrantServiceImpl implements GrantService {

    private static final Logger log = LoggerFactory.getLogger(GrantServiceImpl.class);
    private static final int MAX_RETRY = 3;

    private final GrantEntitlementMapper entitlementMapper;
    private final GrantTaskMapper taskMapper;
    private final GrantTaskDetailMapper detailMapper;
    private final SnowflakeIdGenerator idGen;
    private final GrantDispatchProducer producer;
    private final IotGrantClient iotClient;

    public GrantServiceImpl(GrantEntitlementMapper entitlementMapper,
                            GrantTaskMapper taskMapper,
                            GrantTaskDetailMapper detailMapper,
                            SnowflakeIdGenerator idGen,
                            GrantDispatchProducer producer,
                            IotGrantClient iotClient) {
        this.entitlementMapper = entitlementMapper;
        this.taskMapper = taskMapper;
        this.detailMapper = detailMapper;
        this.idGen = idGen;
        this.producer = producer;
        this.iotClient = iotClient;
    }

    // ==================== 申请 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public GrantVO apply(GrantApplyCmd cmd) {
        String tenantId = TenantContext.tenantId();

        // ---- 1) 基础校验 ----
        LocalDateTime start = cmd.validStart() != null ? cmd.validStart() : LocalDateTime.now();
        LocalDateTime end = cmd.validEnd();
        if (end != null && !end.isAfter(start)) {
            throw BizException.paramInvalid("失效时间必须晚于生效时间");
        }
        if (end == null && !"OWNERSHIP".equals(cmd.grantLevel())) {
            throw BizException.paramInvalid("仅 OWNERSHIP（所有权）允许不设失效时间");
        }

        // ---- 2) 幂等：同人+同空间+同层级+同有效期 只建一次 ----
        String idemKey = idempotentKey(cmd.personId(), cmd.spaceId(), cmd.grantLevel(), start, end);
        GrantTask existTask = taskMapper.selectOne(new LambdaQueryWrapper<GrantTask>()
                .eq(GrantTask::getIdempotentKey, idemKey)
                .last("LIMIT 1"));
        if (existTask != null && !GrantTaskStatus.FAILED.name().equals(existTask.getTaskStatus())) {
            log.info("授权幂等命中，返回已有任务 taskId={}", existTask.getId());
            GrantEntitlement e = entitlementMapper.selectById(existTask.getEntitlementId());
            return GrantVO.from(e);
        }

        // ---- 3) 建权益 ----
        long entId = idGen.nextId();
        GrantEntitlement e = new GrantEntitlement();
        e.setId(entId);
        e.setTenantId(tenantId);
        e.setGrantNo("G" + entId);
        e.setGrantLevel(cmd.grantLevel());
        e.setHolderType("PERSON");
        e.setPersonId(cmd.personId());
        e.setSpaceId(cmd.spaceId());
        e.setValidStart(start);
        e.setValidEnd(end);
        // 所有权不含开门权限（管理权才含），见 DDL 注释
        e.setAllowOpen("OWNERSHIP".equals(cmd.grantLevel()) ? 0 : 1);
        e.setAllowManage("OWNERSHIP".equals(cmd.grantLevel())
                || "MANAGEMENT".equals(cmd.grantLevel()) ? 1 : 0);
        e.setAllowDelegate("OWNERSHIP".equals(cmd.grantLevel()) ? 1 : 0);
        e.setVisitLimitTimes("VISIT".equals(cmd.grantLevel()) ? 1 : null);
        e.setVisitUsedTimes(0);
        e.setSourceType(blankToNull(cmd.sourceType()) == null ? "MANUAL" : cmd.sourceType());
        e.setSourceId(cmd.sourceId());
        e.setGrantStatus(GrantStatus.EFFECTIVE.name());
        e.setRemark(cmd.remark());
        e.setIsDeleted(0);
        entitlementMapper.insert(e);

        // ---- 4) 建任务 ----
        long taskId = idGen.nextId();
        GrantTask t = new GrantTask();
        t.setId(taskId);
        t.setTenantId(tenantId);
        t.setTaskNo("T" + taskId);
        t.setIdempotentKey(idemKey);
        t.setTaskType("GRANT");
        t.setPersonId(cmd.personId());
        t.setEntitlementId(entId);
        t.setKeyringIds(cmd.keyringIds() == null ? null
                : cmd.keyringIds().stream().map(String::valueOf).collect(Collectors.joining(",")));
        t.setLockCount(0);
        t.setSuccessCount(0);
        t.setFailCount(0);
        t.setValidStart(start);
        t.setValidEnd(end);
        t.setTaskStatus(GrantTaskStatus.PENDING.name());
        t.setRetryCount(0);
        t.setTriggerSource("MANUAL");
        t.setCreateTime(LocalDateTime.now());
        taskMapper.insert(t);

        // ---- 5) 投递 MQ（事务提交后生效）----
        producer.publishDispatch(taskId);

        return GrantVO.from(e);
    }

    // ==================== 查询 ====================

    @Override
    public GrantVO get(Long id) {
        GrantEntitlement e = entitlementMapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("权益");
        }
        return GrantVO.from(e);
    }

    @Override
    public PageResult<GrantVO> page(long pageNum, long pageSize, Long personId, Long spaceId,
                                    String grantStatus) {
        LambdaQueryWrapper<GrantEntitlement> qw = new LambdaQueryWrapper<GrantEntitlement>()
                .eq(personId != null, GrantEntitlement::getPersonId, personId)
                .eq(spaceId != null, GrantEntitlement::getSpaceId, spaceId)
                .eq(grantStatus != null && !grantStatus.isBlank(),
                        GrantEntitlement::getGrantStatus, grantStatus)
                .orderByDesc(GrantEntitlement::getId);
        IPage<GrantEntitlement> page =
                entitlementMapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<GrantVO> rows = page.getRecords().stream().map(GrantVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    public GrantTaskVO task(Long taskId) {
        GrantTask t = taskMapper.selectById(taskId);
        if (t == null) {
            throw BizException.notFound("授权任务");
        }
        return GrantTaskVO.from(t);
    }

    /** 任务的逐设备明细。 */
    public List<GrantTaskDetail> details(Long taskId) {
        return detailMapper.selectList(new LambdaQueryWrapper<GrantTaskDetail>()
                .eq(GrantTaskDetail::getTaskId, taskId)
                .orderByAsc(GrantTaskDetail::getId));
    }

    // ==================== 撤销 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public GrantVO revoke(Long id, String reason) {
        GrantEntitlement e = entitlementMapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("权益");
        }
        GrantStatus cur = GrantStatus.valueOf(e.getGrantStatus());
        if (cur.isTerminal()) {
            throw BizException.stateConflict("权益已是终态（" + cur.label() + "），不可撤销");
        }
        if (!GrantStatus.nextOf(cur).contains(GrantStatus.REVOKED)) {
            throw BizException.stateConflict("权益状态 " + cur.label() + " 不允许撤销");
        }
        e.setGrantStatus(GrantStatus.REVOKED.name());
        e.setRevokeReason(reason);
        entitlementMapper.updateById(e);

        // 生成 REVOKE 任务
        long taskId = idGen.nextId();
        GrantTask t = new GrantTask();
        t.setId(taskId);
        t.setTenantId(e.getTenantId());
        t.setTaskNo("T" + taskId);
        t.setIdempotentKey("REVOKE-" + id + "-" + System.currentTimeMillis());
        t.setTaskType("REVOKE");
        t.setPersonId(e.getPersonId());
        t.setEntitlementId(e.getId());
        t.setLockCount(0);
        t.setSuccessCount(0);
        t.setFailCount(0);
        t.setTaskStatus(GrantTaskStatus.PENDING.name());
        t.setRetryCount(0);
        t.setTriggerSource("MANUAL");
        t.setCreateTime(LocalDateTime.now());
        taskMapper.insert(t);
        producer.publishRetry(taskId);

        return GrantVO.from(e);
    }

    // ==================== 下发（异步执行）====================

    @Override
    public void dispatch(Long taskId) {
        GrantTask t = taskMapper.selectById(taskId);
        if (t == null) {
            log.warn("授权任务不存在 taskId={}", taskId);
            return;
        }
        if (GrantTaskStatus.valueOf(t.getTaskStatus()).isFinished()) {
            return;   // 幂等：已结束不重发
        }
        if (t.getRetryCount() != null && t.getRetryCount() >= MAX_RETRY) {
            markFailed(t, "重试次数超过上限(" + MAX_RETRY + ")");
            return;
        }

        // 标记下发中
        t.setTaskStatus(GrantTaskStatus.DISPATCHING.name());
        t.setDispatchTime(LocalDateTime.now());
        t.setUpdateTime(LocalDateTime.now());
        taskMapper.updateById(t);

        try {
            // 目标门锁：暂按 "本租户全部锁" 取（真实实现应按空间树下的设备过滤）
            List<String> lockIds = mockTargetLocks(t);
            boolean isRevoke = "REVOKE".equals(t.getTaskType());

            IotGrantRequest req = new IotGrantRequest(t.getPersonId(), null, null,
                    lockIds, t.getValidStart(), t.getValidEnd(), null, null);
            IotGrantResult r = isRevoke ? iotClient.revoke(req) : iotClient.grant(req);

            if (!r.success()) {
                markRetryOrFail(t, r.message());
                return;
            }

            // 保存 IoT 异步任务号
            if (r.iotTaskId() != null) {
                t.setIotTaskId(r.iotTaskId());
            }
            t.setLockCount(lockIds.size());

            // 逐设备写明细
            List<IotGrantResult.DeviceResult> devs = r.devices().isEmpty()
                    ? lockIds.stream().map(id -> new IotGrantResult.DeviceResult(
                            id, true, null, null, null)).toList()
                    : r.devices();
            int ok = 0;
            int fail = 0;
            LocalDateTime now = LocalDateTime.now();
            List<GrantTaskDetail> details = new ArrayList<>();
            for (IotGrantResult.DeviceResult d : devs) {
                GrantTaskDetail dt = new GrantTaskDetail();
                dt.setId(idGen.nextId());
                dt.setTenantId(t.getTenantId());
                dt.setTaskId(t.getId());
                dt.setLockId(d.lockId());
                dt.setDetailStatus(d.success() ? "SUCCESS" : "FAILED");
                dt.setErrorCode(d.errorCode());
                dt.setErrorMsg(d.errorMsg());
                dt.setDurationMs(d.durationMs());
                dt.setCreateTime(now);
                dt.setUpdateTime(now);
                detailMapper.insert(dt);
                details.add(dt);
                if (d.success()) {
                    ok++;
                } else {
                    fail++;
                }
            }
            t.setSuccessCount(ok);
            t.setFailCount(fail);

            // 终态判定
            if (fail == 0) {
                t.setTaskStatus(GrantTaskStatus.SUCCESS.name());
                t.setFinishTime(now);
                t.setLastError(null);
            } else if (ok == 0) {
                markRetryOrFail(t, devs.isEmpty() ? "无目标设备" : "全部设备失败");
                return;
            } else {
                t.setTaskStatus(GrantTaskStatus.PARTIAL.name());
                t.setFinishTime(now);
            }
            t.setUpdateTime(now);
            taskMapper.updateById(t);
            log.info("授权任务完成 taskId={} status={} ok={} fail={}",
                    t.getId(), t.getTaskStatus(), ok, fail);

        } catch (Exception ex) {
            log.error("授权任务下发异常 taskId={}", taskId, ex);
            markRetryOrFail(t, ex.getMessage());
        }
    }

    // ==================== 内部 ====================

    /** 目标门锁（占位实现：真实逻辑应按空间树 + 设备绑定关系过滤）。 */
    private List<String> mockTargetLocks(GrantTask t) {
        // TODO 待接入 bp_dev_lock 与空间绑定关系后替换
        return List.of("DEV-PLACEHOLDER-1");
    }

    private void markRetryOrFail(GrantTask t, String error) {
        int retry = (t.getRetryCount() == null ? 0 : t.getRetryCount()) + 1;
        t.setRetryCount(retry);
        t.setLastError(truncate(error, 900));
        t.setUpdateTime(LocalDateTime.now());
        if (retry >= MAX_RETRY) {
            t.setTaskStatus(GrantTaskStatus.FAILED.name());
            t.setFinishTime(LocalDateTime.now());
            log.warn("授权任务失败（已达重试上限）taskId={} err={}", t.getId(), error);
        } else {
            t.setTaskStatus(GrantTaskStatus.PENDING.name());
            log.warn("授权任务待重试 taskId={} retry={} err={}", t.getId(), retry, error);
        }
        taskMapper.updateById(t);
    }

    private void markFailed(GrantTask t, String error) {
        t.setTaskStatus(GrantTaskStatus.FAILED.name());
        t.setLastError(truncate(error, 900));
        t.setFinishTime(LocalDateTime.now());
        t.setUpdateTime(LocalDateTime.now());
        taskMapper.updateById(t);
    }

    /** 幂等键：sha1(personId|spaceId|level|validStart|validEnd)。 */
    static String idempotentKey(Long personId, Long spaceId, String level,
                                LocalDateTime start, LocalDateTime end) {
        String raw = personId + "|" + spaceId + "|" + level + "|"
                + (start == null ? "" : start) + "|" + (end == null ? "" : end);
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-1");
            byte[] d = md.digest(raw.getBytes(StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder(40);
            for (byte b : d) {
                sb.append(String.format("%02x", b));
            }
            return sb.toString();
        } catch (Exception ex) {
            throw new IllegalStateException("幂等键计算失败", ex);
        }
    }

    private static String truncate(String s, int max) {
        if (s == null) {
            return null;
        }
        return s.length() <= max ? s : s.substring(0, max);
    }

    private static String blankToNull(String s) {
        return (s == null || s.isBlank()) ? null : s;
    }
}
'''

# ==================== 配置：IoT client 选择 ====================
FILES['grant/config/GrantIotConfig.java'] = '''package com.yundao.bp.grant.config;

import com.yundao.bp.grant.iot.IotGrantClient;
import com.yundao.bp.grant.iot.MockIotGrantClient;
import com.yundao.bp.grant.iot.YmdGrantClient;
import com.yundao.bp.iot.legacy.YmdClient;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * IoT 授权客户端装配。
 *
 * <p>{@code bp.grant.iot-mode}：
 * <ul>
 *   <li>{@code mock}（默认）—— 不真正下发，用于编排验证与演示</li>
 *   <li>{@code real} —— 走真实 IoT 平台（需配置 ymd.iot.* 凭证，且参数需联调确认）</li>
 * </ul>
 */
@Configuration
public class GrantIotConfig {

    private static final Logger log = LoggerFactory.getLogger(GrantIotConfig.class);

    @Bean
    public IotGrantClient iotGrantClient(
            @Value("${bp.grant.iot-mode:mock}") String mode,
            org.springframework.beans.factory.ObjectProvider<YmdClient> ymdClientProvider) {

        if ("real".equalsIgnoreCase(mode)) {
            YmdClient ymd = ymdClientProvider.getIfAvailable();
            if (ymd == null) {
                log.error("bp.grant.iot-mode=real 但未配置 ymd.iot 凭证，降级为 mock");
                return new MockIotGrantClient();
            }
            log.info("IoT 授权客户端 = YmdGrantClient（真实平台）");
            return new YmdGrantClient(ymd);
        }
        log.info("IoT 授权客户端 = MockIotGrantClient（不真正下发）");
        return new MockIotGrantClient();
    }
}
'''

# ==================== 重试任务 ====================
FILES['grant/job/GrantRetryJob.java'] = '''package com.yundao.bp.grant.job;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.grant.constant.GrantTaskStatus;
import com.yundao.bp.grant.entity.GrantTask;
import com.yundao.bp.grant.mapper.GrantTaskMapper;
import com.yundao.bp.grant.mq.GrantDispatchProducer;
import java.time.LocalDateTime;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/**
 * 授权任务兜底重试。
 *
 * <p>解决两类问题：
 * <ol>
 *   <li><b>MQ 投递失败</b>：apply 时 MQ 不可用 → 任务停在 PENDING，这里补投</li>
 *   <li><b>消费者处理丢失</b>：消息被吞 → 任务超时仍在 PENDING，这里补投</li>
 * </ol>
 *
 * <p>只捞 60 秒前创建、且重试次数未超限的 PENDING 任务，避免与正常流程抢跑。
 */
@Component
public class GrantRetryJob {

    private static final Logger log = LoggerFactory.getLogger(GrantRetryJob.class);
    private static final int MAX_RETRY = 3;

    private final GrantTaskMapper taskMapper;
    private final GrantDispatchProducer producer;

    public GrantRetryJob(GrantTaskMapper taskMapper, GrantDispatchProducer producer) {
        this.taskMapper = taskMapper;
        this.producer = producer;
    }

    @Scheduled(fixedDelay = 60_000, initialDelay = 30_000)
    public void retryPending() {
        LocalDateTime before = LocalDateTime.now().minusSeconds(60);
        List<GrantTask> list = taskMapper.selectList(new LambdaQueryWrapper<GrantTask>()
                .eq(GrantTask::getTaskStatus, GrantTaskStatus.PENDING.name())
                .lt(GrantTask::getCreateTime, before)
                .and(w -> w.isNull(GrantTask::getRetryCount)
                        .or().lt(GrantTask::getRetryCount, MAX_RETRY))
                .last("LIMIT 50"));
        if (list.isEmpty()) {
            return;
        }
        log.info("补投 PENDING 授权任务 {} 个", list.size());
        for (GrantTask t : list) {
            producer.publishDispatch(t.getId());
        }
    }
}
'''

# ==================== 控制器 ====================
FILES['grant/controller/GrantController.java'] = '''package com.yundao.bp.grant.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.grant.dto.GrantApplyCmd;
import com.yundao.bp.grant.dto.GrantTaskVO;
import com.yundao.bp.grant.dto.GrantVO;
import com.yundao.bp.grant.entity.GrantTaskDetail;
import com.yundao.bp.grant.service.GrantService;
import com.yundao.bp.grant.service.impl.GrantServiceImpl;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 授权编排接口（BC-04 权益与钥匙）。
 *
 * <p>授权是<b>异步</b>的：POST 返回时任务通常还是 `PENDING`，
 * 需通过 {@code /tasks/{id}} 轮询下发结果。
 */
@RestController
@RequestMapping("/api/v1/grants")
public class GrantController {

    private final GrantService grantService;
    private final GrantServiceImpl grantServiceImpl;

    public GrantController(GrantService grantService, GrantServiceImpl grantServiceImpl) {
        this.grantService = grantService;
        this.grantServiceImpl = grantServiceImpl;
    }

    @PostMapping
    public R<GrantVO> apply(@Valid @RequestBody GrantApplyCmd cmd) {
        return R.ok(grantService.apply(cmd));
    }

    @GetMapping("/{id}")
    public R<GrantVO> get(@PathVariable Long id) {
        return R.ok(grantService.get(id));
    }

    @GetMapping
    public R<PageResult<GrantVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                       @RequestParam(defaultValue = "20") long pageSize,
                                       @RequestParam(required = false) Long personId,
                                       @RequestParam(required = false) Long spaceId,
                                       @RequestParam(required = false) String grantStatus) {
        return R.ok(grantService.page(pageNum, pageSize, personId, spaceId, grantStatus));
    }

    /** 任务状态（轮询用）。 */
    @GetMapping("/tasks/{taskId}")
    public R<GrantTaskVO> task(@PathVariable Long taskId) {
        return R.ok(grantService.task(taskId));
    }

    /** 任务逐设备明细。 */
    @GetMapping("/tasks/{taskId}/details")
    public R<List<GrantTaskDetail>> details(@PathVariable Long taskId) {
        return R.ok(grantServiceImpl.details(taskId));
    }

    @PostMapping("/{id}/revoke")
    public R<GrantVO> revoke(@PathVariable Long id, @RequestBody(required = false) RevokeCmd cmd) {
        return R.ok(grantService.revoke(id, cmd == null ? null : cmd.reason()));
    }

    public record RevokeCmd(String reason) {
    }
}
'''

count = 0
for rel, content in FILES.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个文件' % count)
