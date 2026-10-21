package com.yundao.bp.biz.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 申诉/异议单。对应 {@code bp_biz_appeal}。
 *
 * <p>保障房的法定救济通道：对审核结论、年审核查、公示内容、退出决定不服时提出。
 */
@Data
@TableName("bp_biz_appeal")
public class BizAppeal {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String appealNo;

    /** APPLICATION / REVIEW / ANNUAL_REVIEW / PUBLICITY / EXIT */
    private String bizType;
    private Long bizId;
    private Long personId;
    private Long orgId;

    /** SUBMIT 申诉 / OBJECTION 公示异议 */
    private String appealType;

    private String appealReason;
    private String appealEvidence;

    /** 申诉截止时间（政策时限） */
    private LocalDateTime deadlineTime;
    private LocalDateTime appealTime;

    private LocalDateTime acceptTime;
    private Long acceptUserId;
    private Long handleUserId;
    private LocalDateTime handleTime;

    private String handleResult;
    private String reviewOpinion;

    /** SUBMITTED / ACCEPTED / INVESTIGATING / UPHELD / REJECTED / WITHDRAWN / TIMEOUT */
    private String appealStatus;

    /** RESTORE / CANCEL / ADJUST / NONE */
    private String resultEffect;
    /** PENDING 待告知 / SENT 已告知 */
    private String notifyStatus;

    @TableField(fill = FieldFill.INSERT)
    private String createBy;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private String updateBy;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;

    @TableLogic
    private Integer isDeleted;
}
