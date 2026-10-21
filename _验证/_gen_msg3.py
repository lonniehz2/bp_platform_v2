# -*- coding: utf-8 -*-
"""修正 MessageServiceImpl + 生成消息中心控制器"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'

# 1) 修正不存在的 getRemarkSafe()
p = os.path.join(BASE, r'msg\service\impl\MessageServiceImpl.java')
s = io.open(p, encoding='utf-8').read()
s = s.replace('r.setThirdMsgId("SIM-" + channel + "-" + r.getRemarkSafe());',
              'r.setThirdMsgId("SIM-" + channel + "-" + r.getId());')
io.open(p, 'w', encoding='utf-8').write(s)
print('  ✓ 修正 thirdMsgId 生成')

# 2) 控制器
ctrl = '''package com.yundao.bp.msg.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.msg.dto.MessageSendCmd;
import com.yundao.bp.msg.dto.MessageVO;
import com.yundao.bp.msg.entity.MsgTemplate;
import com.yundao.bp.msg.entity.MsgTodo;
import com.yundao.bp.msg.service.MessageService;
import jakarta.validation.Valid;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 消息中心接口（BC-07）。
 *
 * <p>涵盖：模板管理、消息发送、发送记录、订阅广播、站内待办。
 */
@RestController
@RequestMapping("/api/v1/messages")
public class MessageController {

    private final MessageService service;

    public MessageController(MessageService service) {
        this.service = service;
    }

    // ---------- 发送 ----------

    /** 发送消息（按模板或直发）。 */
    @PostMapping("/send")
    public R<MessageVO> send(@Valid @RequestBody MessageSendCmd cmd) {
        return R.ok(service.send(cmd));
    }

    /** 按业务类型广播给所有订阅者。 */
    @PostMapping("/broadcast")
    public R<Integer> broadcast(@RequestBody BroadcastCmd cmd) {
        return R.ok(service.broadcast(cmd.bizType(), cmd.title(), cmd.content(),
                cmd.bizId()));
    }

    @GetMapping("/records")
    public R<PageResult<MessageVO>> records(@RequestParam(defaultValue = "1") long pageNum,
                                            @RequestParam(defaultValue = "20") long pageSize,
                                            @RequestParam(required = false) String channel,
                                            @RequestParam(required = false) String sendStatus,
                                            @RequestParam(required = false) String receiverId,
                                            @RequestParam(required = false) String bizType) {
        return R.ok(service.pageSendRecords(pageNum, pageSize, channel, sendStatus, receiverId,
                bizType));
    }

    /** 重投失败消息。 */
    @PostMapping("/retry-failed")
    public R<Integer> retryFailed(@RequestParam(defaultValue = "20") int limit) {
        return R.ok(service.retryFailed(limit));
    }

    // ---------- 模板 ----------

    @GetMapping("/templates")
    public R<List<MsgTemplate>> templates(@RequestParam(required = false) String bizType,
                                          @RequestParam(required = false) String channel) {
        return R.ok(service.listTemplates(bizType, channel));
    }

    @PostMapping("/templates")
    public R<MsgTemplate> saveTemplate(@RequestBody TemplateCmd cmd) {
        return R.ok(service.saveTemplate(cmd.templateCode(), cmd.templateName(), cmd.channel(),
                cmd.bizType(), cmd.titleTpl(), cmd.contentTpl()));
    }

    /** 模板渲染预览（校验变量是否齐全）。 */
    @PostMapping("/templates/{code}/render")
    public R<String> render(@PathVariable String code,
                            @RequestBody(required = false) Map<String, Object> vars) {
        return R.ok(service.render(code, vars));
    }

    // ---------- 待办 ----------

    @PostMapping("/todos")
    public R<MsgTodo> createTodo(@RequestBody TodoCreateCmd cmd) {
        return R.ok(service.createTodo(cmd.userId(), cmd.todoType(), cmd.title(), cmd.content(),
                cmd.bizType(), cmd.bizId(), cmd.priority()));
    }

    @GetMapping("/todos")
    public R<PageResult<MsgTodo>> todos(@RequestParam(defaultValue = "1") long pageNum,
                                        @RequestParam(defaultValue = "20") long pageSize,
                                        @RequestParam(required = false) Long userId,
                                        @RequestParam(required = false) String status,
                                        @RequestParam(required = false) String todoType) {
        return R.ok(service.pageTodos(pageNum, pageSize, userId, status, todoType));
    }

    /** 未读数量（红点）。 */
    @GetMapping("/todos/unread")
    public R<Long> unread(@RequestParam Long userId) {
        return R.ok(service.unreadCount(userId));
    }

    @PostMapping("/todos/{id}/read")
    public R<MsgTodo> read(@PathVariable Long id) {
        return R.ok(service.markRead(id));
    }

    @PostMapping("/todos/{id}/done")
    public R<MsgTodo> done(@PathVariable Long id) {
        return R.ok(service.markDone(id));
    }

    public record BroadcastCmd(String bizType, String title, String content, Long bizId) {
    }

    public record TemplateCmd(String templateCode, String templateName, String channel,
                              String bizType, String titleTpl, String contentTpl) {
    }

    public record TodoCreateCmd(Long userId, String todoType, String title, String content,
                                String bizType, Long bizId, String priority) {
    }
}
'''
p2 = os.path.join(BASE, r'msg\controller\MessageController.java')
os.makedirs(os.path.dirname(p2), exist_ok=True)
io.open(p2, 'w', encoding='utf-8').write(ctrl)
print('  + msg/controller/MessageController.java')
