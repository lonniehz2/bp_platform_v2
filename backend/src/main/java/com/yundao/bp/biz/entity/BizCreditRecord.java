package com.yundao.bp.biz.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 信用惩戒记录。对应 {@code bp_biz_credit_record}。
 *
 * <p>⭐ 保障房「失信惩戒」是核心管理抓手：转租出借、提供虚假信息等行为
 * 会被记录并<b>限制再申请年限</b>（政策常见 5 年）。
 */
@Data
@TableName("bp_biz_credit_record")
public class BizCreditRecord {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String recordNo;

    private Long personId;

    /** EXIT / CONTRACT / APPLICATION */
    private String bizType;
    private Long bizId;

    /** FALSE_INFO / SUBLEASE / STRUCTURE / CHANGE_USE / VACANT / ILLEGAL / ARREARS / OTHER */
    private String violationType;
    private String violationDesc;
    private String evidenceUrl;

    /** TERMINATE / BAN_APPLY / CREDIT_PLATFORM / FINE / OTHER */
    private String sanctionType;
    /** 限制申请年限 */
    private Integer banYears;
    private LocalDate banStartDate;
    private LocalDate banEndDate;

    private String pushPlatform;
    /** PENDING / PUSHED / FAILED / NONE */
    private String pushStatus;
    private LocalDateTime pushTime;

    private Long decideOrgId;
    private Long decideUserId;
    private LocalDateTime decideTime;
    private String legalDocNo;

    /** EFFECTIVE / EXPIRED / REVOKED */
    private String status;
    private String remark;

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
