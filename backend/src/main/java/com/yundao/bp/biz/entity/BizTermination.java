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
 * 退租/腾退单。对应 {@code bp_biz_termination}。
 */
@Data
@TableName("bp_biz_termination")
public class BizTermination {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String terminationNo;

    private Long contractId;
    private Long houseId;
    private Long personId;

    /** NORMAL / EXPEL / EXPIRE / EXCHANGE / OTHER */
    private String terminationType;

    private LocalDateTime applyTime;
    private LocalDate planExitDate;
    private LocalDate actualExitDate;
    private String exitReason;

    /** PENDING / PASSED / ABNORMAL */
    private String inspectStatus;
    private String inspectResult;
    private String inspectImages;

    private BigDecimal damageAmount;
    /** 结算金额（正数退还，负数补缴） */
    private BigDecimal settleAmount;
    private BigDecimal depositRefund;
    private BigDecimal arrearsAmount;

    /** PENDING / SETTLED / WAIVED */
    private String settleStatus;

    /** APPLYING / APPROVING / APPROVED / REJECTED / COMPLETED / CANCELLED */
    private String terminationStatus;

    private Integer houseReleased;
    private Integer grantRevoked;

    /** 重庆：腾退过渡期 */
    private LocalDate transitionStartDate;
    private LocalDate transitionEndDate;
    private Integer transitionMonths;
    /** 重庆：期内 1.5，期满 2.0 */
    private BigDecimal transitionRentMultiplier;

    /** 成都：搬迁期（不超过 6 个月） */
    private LocalDate relocationStartDate;
    private LocalDate relocationEndDate;

    private Integer enforceFlag;
    private LocalDate enforceApplyDate;
    private String enforceCourt;
    private String enforceResult;

    /** 成都：承租人可指定物品处置人 */
    private String itemHandlerName;
    private String itemHandlerPhone;
    private Integer notaryFlag;
    private String notaryNo;

    /** 违规退回：限制再申请结束日 */
    private LocalDate banReapplyEndDate;

    private String createBy;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.UPDATE)
    private String updateBy;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
