package com.yundao.bp.iam.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 登录会话。对应 `bp_iam_session`。
 */
@Data
@TableName("bp_iam_session")
public class IamSession {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private Long userId;
    /** 令牌标识（随机串，DB 可撤销） */
    private String tokenId;
    /** WEB / APP / MINIAPP / SCREEN */
    private String deviceType;
    private String deviceId;
    private String loginIp;
    private LocalDateTime loginTime;
    private LocalDateTime expireTime;
    /** ACTIVE / LOGOUT / KICKED / EXPIRED */
    private String status;
}
