package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 欠费停权处置记录。对应 {@code bp_fin_arrears_action}。
 */
@Data
@TableName("bp_fin_arrears_action")
public class FinArrearsAction {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String actionNo;

    /** 组织：供按组织筛选 */
    private Long orgId;

    private Long contractId;
    private Long personId;

    private BigDecimal arrearsAmount;
    private Integer overdueDays;

    /** AUTO / MANUAL */
    private String triggerType;
    /** NOTIFY / FREEZE / UNFREEZE / RESTRICT / EXPIRE / LEGAL */
    private String actionType;
    /** ALL / ROOM_LOCK / EXCLUDE_MAIN_DOOR */
    private String freezeScope;

    /** PENDING / EXECUTED / REVOKED / FAILED */
    private String actionStatus;
    private LocalDateTime executeTime;
    private Long grantTaskId;
    private String revokeReason;

    @TableField(fill = FieldFill.INSERT)
    private String createBy;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
