package com.yundao.bp.msg.controller;

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
import org.springframework.format.annotation.DateTimeFormat;

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
    @com.yundao.bp.iam.security.RequirePerm("messages:send:send")
    @PostMapping("/send")
    public R<MessageVO> send(@Valid @RequestBody MessageSendCmd cmd) {
        return R.ok(service.send(cmd));
    }

    /** 按业务类型广播给所有订阅者。 */
    @com.yundao.bp.iam.security.RequirePerm("messages:broadcast:broadcast")
    @PostMapping("/broadcast")
    public R<Integer> broadcast(@RequestBody BroadcastCmd cmd) {
        return R.ok(service.broadcast(cmd.bizType(), cmd.title(), cmd.content(),
                cmd.bizId()));
    }

    @com.yundao.bp.iam.security.RequirePerm("messages:records:record")
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
    @com.yundao.bp.iam.security.RequirePerm("messages:retry-failed:create")
    @PostMapping("/retry-failed")
    public R<Integer> retryFailed(@RequestParam(defaultValue = "20") int limit) {
        return R.ok(service.retryFailed(limit));
    }

    // ---------- 模板 ----------

    @com.yundao.bp.iam.security.RequirePerm("messages:templates:view")
    @GetMapping("/templates")
    public R<List<MsgTemplate>> templates(@RequestParam(required = false) String bizType,
                                          @RequestParam(required = false) String channel) {
        return R.ok(service.listTemplates(bizType, channel));
    }

    @com.yundao.bp.iam.security.RequirePerm("messages:templates:create")
    @PostMapping("/templates")
    public R<MsgTemplate> saveTemplate(@RequestBody TemplateCmd cmd) {
        return R.ok(service.saveTemplate(cmd.templateCode(), cmd.templateName(), cmd.channel(),
                cmd.bizType(), cmd.titleTpl(), cmd.contentTpl()));
    }

    /** 模板渲染预览（校验变量是否齐全）。 */
    @com.yundao.bp.iam.security.RequirePerm("messages:templates:create")
    @PostMapping("/templates/{code}/render")
    public R<String> render(@PathVariable String code,
                            @RequestBody(required = false) Map<String, Object> vars) {
        return R.ok(service.render(code, vars));
    }

    // ---------- 待办 ----------

    @com.yundao.bp.iam.security.RequirePerm("messages:todo:create")
    @PostMapping("/todos")
    public R<MsgTodo> createTodo(@RequestBody TodoCreateCmd cmd) {
        return R.ok(service.createTodo(cmd.userId(), cmd.todoType(), cmd.title(), cmd.content(),
                cmd.bizType(), cmd.bizId(), cmd.priority()));
    }

    @com.yundao.bp.iam.security.RequirePerm("messages:todo:view")
    @GetMapping("/todos")
    public R<PageResult<MsgTodo>> todos(@RequestParam(defaultValue = "1") long pageNum,
                                        @RequestParam(defaultValue = "20") long pageSize,
                                        @RequestParam(required = false) Long userId,
                                        @RequestParam(required = false) String status,
                                        @RequestParam(required = false) String todoType,
                                        @RequestParam(required = false) String keyword,
                                        @RequestParam(required = false)
                                        @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
                                        java.time.LocalDate startDate,
                                        @RequestParam(required = false)
                                        @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
                                        java.time.LocalDate endDate) {
        return R.ok(service.pageTodos(pageNum, pageSize, userId, status, todoType,
                keyword, startDate, endDate));
    }

    /** 未读数量（红点）。 */
    @com.yundao.bp.iam.security.RequirePerm("messages:todo:read")
    @GetMapping("/todos/unread")
    public R<Long> unread(@RequestParam Long userId) {
        return R.ok(service.unreadCount(userId));
    }

    @com.yundao.bp.iam.security.RequirePerm("messages:todo:read")
    @PostMapping("/todos/{id}/read")
    public R<MsgTodo> read(@PathVariable Long id) {
        return R.ok(service.markRead(id));
    }

    @com.yundao.bp.iam.security.RequirePerm("messages:todo:done")
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
