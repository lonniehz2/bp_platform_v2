package com.yundao.bp.grant.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 权益（授权）主表。对应 {@code bp_grant_entitlement}。
 *
 * <p>一条权益 = 某个持有者对某个空间/房源在某个时段内的权限集合。
 */
@Data
@TableName("bp_grant_entitlement")
public class GrantEntitlement {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String grantNo;

    /** OWNERSHIP / MANAGEMENT / USAGE / VISIT */
    private String grantLevel;
    /** PERSON / ORG */
    private String holderType;
    private Long personId;
    private Long orgId;

    /** 权限锚点空间（向下继承） */
    private Long spaceId;
    private String spacePath;
    private Long houseId;

    private LocalDateTime validStart;
    private LocalDateTime validEnd;

    private Integer allowOpen;
    private Integer allowManage;
    private Integer allowDelegate;

    private Integer visitLimitTimes;
    private Integer visitUsedTimes;

    /** CONTRACT / TRANSFER / DELEGATE / ... */
    private String sourceType;
    private Long sourceId;
    private Long parentGrantId;

    /** PENDING / EFFECTIVE / EXPIRED / FROZEN / REVOKED */
    private String grantStatus;
    private String freezeReason;
    private String revokeReason;
    private String remark;

    @TableLogic
    private Integer isDeleted;

    @TableField(fill = FieldFill.INSERT)
    private String createBy;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private String updateBy;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
