package com.yundao.bp.biz.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 轮候库记录。对应 {@code bp_biz_waiting_queue}。
 */
@Data
@TableName("bp_biz_waiting_queue")
public class BizWaitingQueue {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private Long personId;
    private Long applicationId;
    private String securityType;
    private Long orgId;

    private String waitingNo;
    /** 轮候排名（按总分动态计算） */
    private Integer waitingRank;
    /** 总得分 = 优先分 + 轮候时长分 */
    private BigDecimal totalScore;
    private BigDecimal priorityScore;
    private Integer waitDays;

    private LocalDateTime enterTime;
    private LocalDate validUntil;

    /** WAITING / WON / ALLOCATED / FROZEN / EXITED / EXPIRED */
    private String queueStatus;
    private String freezeReason;

    @TableField(fill = FieldFill.INSERT)
    private String createBy;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private String updateBy;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
