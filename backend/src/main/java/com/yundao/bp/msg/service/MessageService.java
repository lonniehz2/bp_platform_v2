package com.yundao.bp.msg.service;

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

    /**
     * 待办分页。
     *
     * @param status    待办状态：PENDING / DONE
     * @param todoType  待办类型
     * @param keyword   标题或内容模糊匹配
     * @param startDate 创建时间起（含）
     * @param endDate   创建时间止（含当天）
     */
    PageResult<MsgTodo> pageTodos(long pageNum, long pageSize, Long userId, String status,
                                  String todoType, String keyword,
                                  java.time.LocalDate startDate, java.time.LocalDate endDate);

    /** 未读数量（红点）。 */
    long unreadCount(Long userId);

    MsgTodo markRead(Long id);

    MsgTodo markDone(Long id);
}
