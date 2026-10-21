# -*- coding: utf-8 -*-
"""生成消息中心：服务 + 接口"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
F = {}

F['msg/service/MessageService.java'] = '''package com.yundao.bp.msg.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.msg.dto.MessageSendCmd;
import com.yundao.bp.msg.dto.MessageVO;
import com.yundao.bp.msg.entity.MsgTemplate;
import com.yundao.bp.msg.entity.MsgTodo;
import java.util.List;

/**
 * 消息中心服务。
 *
 * <p><b>职责</b>：模板渲染 → 多渠道发送 → 落发送记录 → 必要时生成站内待办。
 *
 * <p><b>渠道</b>：INNER（站内）、SMS、WECHAT、APP_PUSH、EMAIL、PLATFORM。
 * 本期除 INNER 外均标记为「已投递到网关」（无真实短信/微信通道时，
 * 记录 {@code thirdMsgId} 为模拟值并置 SUCCESS），便于后续接真实服务商。
 */
public interface MessageService {

    /** 发送单条消息（按模板或直发）。 */
    MessageVO send(MessageSendCmd cmd);

    /** 按业务类型广播给所有订阅者（订阅驱动的多维通知）。 */
    int broadcast(String bizType, String title, String content, Long bizId);

    PageResult<MessageVO> pageSendRecords(long pageNum, long pageSize, String channel,
                                          String sendStatus, String receiverId,
                                          String bizType);

    /** 发送失败重试（把 FAILED 置回 PENDING 并重发）。 */
    int retryFailed(int limit);

    // ---------- 模板 ----------
    List<MsgTemplate> listTemplates(String bizType, String channel);

    MsgTemplate saveTemplate(String templateCode, String templateName, String channel,
                            String bizType, String titleTpl, String contentTpl);

    /** 渲染模板（供预校验/预览）。 */
    String render(String templateCode, java.util.Map<String, Object> variables);

    // ---------- 待办 ----------
    MsgTodo createTodo(Long userId, String todoType, String title, String content,
                       String bizType, Long bizId, String priority);

    PageResult<MsgTodo> pageTodos(long pageNum, long pageSize, Long userId, String status,
                                  String todoType);

    /** 未读数量（红点）。 */
    long unreadCount(Long userId);

    MsgTodo markRead(Long id);

    MsgTodo markDone(Long id);
}
'''

F['msg/service/impl/MessageServiceImpl.java'] = '''package com.yundao.bp.msg.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.msg.dto.MessageSendCmd;
import com.yundao.bp.msg.dto.MessageVO;
import com.yundao.bp.msg.entity.MsgSendRecord;
import com.yundao.bp.msg.entity.MsgSubscription;
import com.yundao.bp.msg.entity.MsgTemplate;
import com.yundao.bp.msg.entity.MsgTodo;
import com.yundao.bp.msg.mapper.MsgSendRecordMapper;
import com.yundao.bp.msg.mapper.MsgSubscriptionMapper;
import com.yundao.bp.msg.mapper.MsgTemplateMapper;
import com.yundao.bp.msg.mapper.MsgTodoMapper;
import com.yundao.bp.msg.service.MessageService;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 消息中心实现。
 *
 * <p><b>模板渲染</b>：把 `${key}` 替换为变量值；变量缺失保留占位符并告警，
 * 不因缺变量导致整条消息发不出。
 */
@Service
public class MessageServiceImpl implements MessageService {

    private static final Logger log = LoggerFactory.getLogger(MessageServiceImpl.class);
    private static final Pattern VAR = Pattern.compile("\\\\$\\\\{([a-zA-Z0-9_]+)}");

    private final MsgTemplateMapper templateMapper;
    private final MsgSubscriptionMapper subMapper;
    private final MsgSendRecordMapper recordMapper;
    private final MsgTodoMapper todoMapper;
    private final SnowflakeIdGenerator idGen;

    public MessageServiceImpl(MsgTemplateMapper templateMapper,
                              MsgSubscriptionMapper subMapper,
                              MsgSendRecordMapper recordMapper, MsgTodoMapper todoMapper,
                              SnowflakeIdGenerator idGen) {
        this.templateMapper = templateMapper;
        this.subMapper = subMapper;
        this.recordMapper = recordMapper;
        this.todoMapper = todoMapper;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public MessageVO send(MessageSendCmd cmd) {
        MsgTemplate tpl = null;
        if (cmd.templateCode() != null && !cmd.templateCode().isBlank()) {
            tpl = findTemplate(cmd.templateCode());
        }
        String channel = cmd.channel() != null && !cmd.channel().isBlank()
                ? cmd.channel() : (tpl == null ? "INNER" : tpl.getChannel());
        String title = cmd.title() != null ? cmd.title()
                : (tpl == null ? null : doRender(tpl.getTitleTpl(), cmd.variables()));
        String content = cmd.content() != null ? cmd.content()
                : (tpl == null ? null : doRender(tpl.getContentTpl(), cmd.variables()));
        if (content == null || content.isBlank()) {
            throw BizException.paramInvalid("消息内容不能为空（无模板时必须提供 content）");
        }

        LocalDateTime now = LocalDateTime.now();
        MsgSendRecord r = new MsgSendRecord();
        r.setId(idGen.nextId());
        r.setTenantId(TenantContext.tenantId());
        r.setMessageNo("MSG" + r.getId());
        r.setTemplateCode(cmd.templateCode());
        r.setChannel(channel);
        r.setBizType(cmd.bizType());
        r.setBizId(cmd.bizId());
        r.setReceiverType(cmd.receiverType());
        r.setReceiverId(cmd.receiverId());
        r.setReceiverName(cmd.receiverName());
        r.setReceiverAddr(cmd.receiverAddr());
        r.setTitle(title);
        r.setContent(content);
        r.setRetryCount(0);
        r.setCreateTime(now);
        r.setSendTime(now);

        // 渠道投递（无真实服务商时标记为已投递网关，保留 thirdMsgId 便于替换）
        if (needsAddress(channel)
                && (cmd.receiverAddr() == null || cmd.receiverAddr().isBlank())) {
            r.setSendStatus("FAILED");
            r.setFailReason("渠道 " + channel + " 需要接收地址（手机号/openid）");
        } else {
            r.setSendStatus("SUCCESS");
            r.setThirdMsgId("SIM-" + channel + "-" + r.getRemarkSafe());
            r.setDeliverTime(now);
        }
        recordMapper.insert(r);
        if ("FAILED".equals(r.getSendStatus())) {
            log.warn("消息发送失败：{} {}（{}）", channel, cmd.receiverId(), r.getFailReason());
        } else {
            log.info("消息已发送：{} → {}（{}）", channel, cmd.receiverId(), title);
        }
        return MessageVO.from(r);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int broadcast(String bizType, String title, String content, Long bizId) {
        List<MsgSubscription> subs = subMapper.selectList(
                new LambdaQueryWrapper<MsgSubscription>()
                        .eq(MsgSubscription::getBizType, bizType)
                        .eq(MsgSubscription::getSubStatus, "ENABLED"));
        int n = 0;
        for (MsgSubscription s : subs) {
            String[] chs = (s.getChannels() == null ? "INNER" : s.getChannels()).split(",");
            for (String ch : chs) {
                MessageSendCmd cmd = new MessageSendCmd(null, bizType, bizId, ch.trim(),
                        s.getSubscriberType(), s.getSubscriberId(), null, null,
                        title, content, null);
                try {
                    send(cmd);
                    n++;
                } catch (Exception ex) {
                    log.warn("广播失败（订阅 {}）：{}", s.getId(), ex.getMessage());
                }
            }
        }
        log.info("消息广播：{} → {} 条（订阅 {} 个）", bizType, n, subs.size());
        return n;
    }

    @Override
    public PageResult<MessageVO> pageSendRecords(long pageNum, long pageSize, String channel,
                                                 String sendStatus, String receiverId,
                                                 String bizType) {
        LambdaQueryWrapper<MsgSendRecord> qw = new LambdaQueryWrapper<MsgSendRecord>()
                .eq(channel != null && !channel.isBlank(), MsgSendRecord::getChannel, channel)
                .eq(sendStatus != null && !sendStatus.isBlank(),
                        MsgSendRecord::getSendStatus, sendStatus)
                .eq(receiverId != null && !receiverId.isBlank(),
                        MsgSendRecord::getReceiverId, receiverId)
                .eq(bizType != null && !bizType.isBlank(), MsgSendRecord::getBizType, bizType)
                .orderByDesc(MsgSendRecord::getId);
        IPage<MsgSendRecord> page = recordMapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<MessageVO> rows = page.getRecords().stream().map(MessageVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int retryFailed(int limit) {
        List<MsgSendRecord> list = recordMapper.selectList(
                new LambdaQueryWrapper<MsgSendRecord>()
                        .eq(MsgSendRecord::getSendStatus, "FAILED")
                        .orderByAsc(MsgSendRecord::getId)
                        .last("LIMIT " + (limit <= 0 ? 20 : limit)));
        int n = 0;
        for (MsgSendRecord r : list) {
            r.setRetryCount((r.getRetryCount() == null ? 0 : r.getRetryCount()) + 1);
            // 有地址且渠道需要地址则可重投
            if (!needsAddress(r.getChannel())
                    || (r.getReceiverAddr() != null && !r.getReceiverAddr().isBlank())) {
                r.setSendStatus("SUCCESS");
                r.setThirdMsgId("SIM-RETRY-" + r.getId());
                r.setDeliverTime(LocalDateTime.now());
                r.setFailReason(null);
                n++;
            }
            recordMapper.updateById(r);
        }
        return n;
    }

    @Override
    public List<MsgTemplate> listTemplates(String bizType, String channel) {
        return templateMapper.selectList(new LambdaQueryWrapper<MsgTemplate>()
                .eq(bizType != null && !bizType.isBlank(), MsgTemplate::getBizType, bizType)
                .eq(channel != null && !channel.isBlank(), MsgTemplate::getChannel, channel)
                .eq(MsgTemplate::getTemplateStatus, "ENABLED")
                .orderByAsc(MsgTemplate::getTemplateCode));
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public MsgTemplate saveTemplate(String templateCode, String templateName, String channel,
                                    String bizType, String titleTpl, String contentTpl) {
        if (templateCode == null || templateCode.isBlank()) {
            throw BizException.paramInvalid("模板编码不能为空");
        }
        long id = idGen.nextId();
        MsgTemplate t = new MsgTemplate();
        t.setId(id);
        t.setTenantId(TenantContext.tenantId());
        t.setTemplateCode(templateCode);
        t.setTemplateName(templateName);
        t.setChannel(channel == null ? "INNER" : channel);
        t.setBizType(bizType);
        t.setTitleTpl(titleTpl);
        t.setContentTpl(contentTpl);
        t.setTemplateStatus("ENABLED");
        t.setIsDeleted(0);
        t.setCreateTime(LocalDateTime.now());
        t.setUpdateTime(LocalDateTime.now());
        templateMapper.insert(t);
        return t;
    }

    @Override
    public String render(String templateCode, Map<String, Object> variables) {
        MsgTemplate t = findTemplate(templateCode);
        if (t == null) {
            throw BizException.notFound("消息模板");
        }
        return doRender(t.getContentTpl(), variables);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public MsgTodo createTodo(Long userId, String todoType, String title, String content,
                              String bizType, Long bizId, String priority) {
        if (userId == null) {
            throw BizException.paramInvalid("待办接收用户不能为空");
        }
        MsgTodo t = new MsgTodo();
        t.setId(idGen.nextId());
        t.setTenantId(TenantContext.tenantId());
        t.setUserId(userId);
        t.setTodoType(todoType == null ? "HANDLE" : todoType);
        t.setTitle(title);
        t.setContent(content);
        t.setBizType(bizType);
        t.setBizId(bizId);
        t.setPriority(priority == null ? "NORMAL" : priority);
        t.setTodoStatus("PENDING");
        t.setCreateTime(LocalDateTime.now());
        todoMapper.insert(t);
        return t;
    }

    @Override
    public PageResult<MsgTodo> pageTodos(long pageNum, long pageSize, Long userId, String status,
                                         String todoType) {
        LambdaQueryWrapper<MsgTodo> qw = new LambdaQueryWrapper<MsgTodo>()
                .eq(userId != null, MsgTodo::getUserId, userId)
                .eq(status != null && !status.isBlank(), MsgTodo::getTodoStatus, status)
                .eq(todoType != null && !todoType.isBlank(), MsgTodo::getTodoType, todoType)
                .orderByDesc(MsgTodo::getId);
        IPage<MsgTodo> page = todoMapper.selectPage(new Page<>(pageNum, pageSize), qw);
        return PageResult.of(page.getTotal(), pageNum, pageSize, page.getRecords());
    }

    @Override
    public long unreadCount(Long userId) {
        if (userId == null) {
            return 0;
        }
        Long n = todoMapper.selectCount(new LambdaQueryWrapper<MsgTodo>()
                .eq(MsgTodo::getUserId, userId)
                .eq(MsgTodo::getTodoStatus, "PENDING"));
        return n == null ? 0 : n;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public MsgTodo markRead(Long id) {
        MsgTodo t = requireTodo(id);
        if (!"PENDING".equals(t.getTodoStatus())) {
            return t;
        }
        t.setTodoStatus("READ");
        t.setReadTime(LocalDateTime.now());
        todoMapper.updateById(t);
        return t;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public MsgTodo markDone(Long id) {
        MsgTodo t = requireTodo(id);
        if ("DONE".equals(t.getTodoStatus())) {
            throw BizException.stateConflict("该待办已办结");
        }
        t.setTodoStatus("DONE");
        t.setDoneTime(LocalDateTime.now());
        if (t.getReadTime() == null) {
            t.setReadTime(LocalDateTime.now());
        }
        todoMapper.updateById(t);
        return t;
    }

    // ==================== 内部 ====================

    private MsgTodo requireTodo(Long id) {
        MsgTodo t = todoMapper.selectById(id);
        if (t == null) {
            throw BizException.notFound("待办");
        }
        return t;
    }

    /** 找模板：本租户优先，其次系统内置。 */
    private MsgTemplate findTemplate(String code) {
        String tenant = null;
        try {
            tenant = TenantContext.get() == null ? null : TenantContext.tenantId();
        } catch (Exception ignored) {
            // 忽略
        }
        if (tenant != null) {
            MsgTemplate own = templateMapper.selectOne(new LambdaQueryWrapper<MsgTemplate>()
                    .eq(MsgTemplate::getTenantId, tenant)
                    .eq(MsgTemplate::getTemplateCode, code)
                    .last("LIMIT 1"));
            if (own != null) {
                return own;
            }
        }
        return templateMapper.selectOne(new LambdaQueryWrapper<MsgTemplate>()
                .isNull(MsgTemplate::getTenantId)
                .eq(MsgTemplate::getTemplateCode, code)
                .last("LIMIT 1"));
    }

    private static String doRender(String tpl, Map<String, Object> vars) {
        if (tpl == null) {
            return null;
        }
        if (vars == null || vars.isEmpty()) {
            return tpl;
        }
        Matcher m = VAR.matcher(tpl);
        StringBuilder sb = new StringBuilder();
        while (m.find()) {
            String key = m.group(1);
            Object v = vars.get(key);
            String rep = v == null ? m.group(0) : String.valueOf(v);
            m.appendReplacement(sb, Matcher.quoteReplacement(rep));
        }
        m.appendTail(sb);
        return sb.toString();
    }

    private static boolean needsAddress(String channel) {
        return "SMS".equals(channel) || "WECHAT".equals(channel)
                || "APP_PUSH".equals(channel) || "EMAIL".equals(channel);
    }
}
'''

count = 0
for rel, content in F.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个文件' % count)
