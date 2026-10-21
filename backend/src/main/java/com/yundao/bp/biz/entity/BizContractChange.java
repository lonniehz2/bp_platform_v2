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
 * 合同变更。对应 {@code bp_biz_contract_change}。
 *
 * <p>{@code before_json} / {@code after_json} 保存变更前后关键字段，
 * 保证任何调价都可追溯、可审计。
 */
@Data
@TableName("bp_biz_contract_change")
public class BizContractChange {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private Long contractId;
    private Long newContractId;

    /** RENEW / RENT_ADJUST / PERIOD / LESSEE / OTHER */
    private String changeType;
    private String changeReason;

    /** 变更前关键字段 JSON */
    private String beforeJson;
    /** 变更后关键字段 JSON */
    private String afterJson;

    /** PENDING / APPROVED / REJECTED */
    private String approveStatus;
    private LocalDate effectiveDate;

    @TableField(fill = FieldFill.INSERT)
    private String createBy;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
