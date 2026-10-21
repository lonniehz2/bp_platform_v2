package com.yundao.bp.biz.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 年审（复核）。对应 {@code bp_biz_annual_review}。
 */
@Data
@TableName("bp_biz_annual_review")
public class BizAnnualReview {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String reviewNo;

    private Long personId;
    private Long contractId;
    private Long houseId;

    /** 复核年度，如 2026 */
    private String reviewYear;
    private String reviewBatch;

    /** ANNUAL / DYNAMIC / SPECIAL */
    private String reviewType;
    private String triggerReason;
    /** 核验结果明细 JSON */
    private String checkResult;

    /** KEEP / ADJUST / EXIT / PENDING */
    private String reviewResult;
    private String adjustContent;

    /** PENDING / REVIEWING / DONE / OVERDUE */
    private String reviewStatus;
    private LocalDate reviewDate;
    private LocalDate nextReviewDate;
    private Long reviewUserId;

    @TableField(fill = FieldFill.INSERT)
    private String createBy;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private String updateBy;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
