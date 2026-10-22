package com.yundao.bp.ops.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/** 物业巡检计划（按周期自动生成工单）。 */
@Data
@TableName("bp_ops_inspection_plan")
public class OpsInspectionPlan {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private Long orgId;
    private Long spaceId;
    private String planName;

    /** SAFETY / EQUIPMENT / CLEANING / GREEN */
    private String inspectType;

    /** DAY / WEEK / MONTH */
    private String frequency;

    private LocalDate nextRunDate;
    private Long assignUserId;
    private String assignUserName;
    private String planStatus;
    private String remark;
    private String createBy;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
    private Integer isDeleted;
}
