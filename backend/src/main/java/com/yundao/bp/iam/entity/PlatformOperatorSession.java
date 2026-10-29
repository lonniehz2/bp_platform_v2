package com.yundao.bp.iam.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/** 运营超管会话。 */
@Data
@TableName("bp_iam_platform_operator_session")
public class PlatformOperatorSession {
    @TableId(type = IdType.INPUT)
    private Long id;
    private Long operatorId;
    private String token;
    private String status;
    private LocalDateTime expireTime;
    private LocalDateTime createTime;
}
