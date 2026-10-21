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
 * 公示。对应 {@code bp_biz_publicity}。
 */
@Data
@TableName("bp_biz_publicity")
public class BizPublicity {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String publicityNo;

    /** QUALIFY / ALLOCATION / EXIT */
    private String publicityType;
    private Long orgId;

    private String title;
    private String content;
    private LocalDate startDate;
    private LocalDate endDate;
    private String attachmentUrl;

    /** DRAFT / PUBLISHED / CLOSED */
    private String publicityStatus;

    @TableField(fill = FieldFill.INSERT)
    private String createBy;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
