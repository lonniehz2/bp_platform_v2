package com.yundao.bp.iam.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/** 平台运营审计。 */
@Data
@TableName("bp_iam_platform_audit")
public class PlatformAudit {
    @TableId(type = IdType.INPUT)
    private Long id;
    private Long operatorId;
    private String operatorName;
    private String platformCode;
    private String action;
    private String detail;
    private String ip;
    private LocalDateTime createTime;
}
