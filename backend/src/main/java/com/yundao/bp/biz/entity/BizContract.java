package com.yundao.bp.biz.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 合同（全生命周期）。对应 {@code bp_biz_contract}。
 */
@Data
@TableName("bp_biz_contract")
public class BizContract {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String contractNo;

    /** PUBLIC_RENTAL / AFFORDABLE / TALENT / LEASE / SERVICE / DORMITORY */
    private String contractType;
    private Long templateId;
    private Long allocationId;

    private Long orgId;
    private Long accountSetId;

    private Long lesseePersonId;
    private String lesseeName;
    private String lesseePhone;
    private String lesseeIdCardMask;
    private Long lessorOrgId;

    private Long houseId;
    private Long spaceId;
    private String houseAddress;
    private BigDecimal houseArea;

    private LocalDate leaseStart;
    private LocalDate leaseEnd;
    private Integer leaseMonths;

    private BigDecimal rentPrice;
    private String rentUnit;
    private BigDecimal monthlyRent;
    private BigDecimal depositAmount;
    private BigDecimal subsidyAmount;
    /** 实付月租金 = 月租金 - 月补贴 */
    private BigDecimal actualPay;

    /** MONTH / QUARTER / HALF_YEAR / YEAR */
    private String payCycle;
    private Integer payDay;
    private BigDecimal lateFeeRate;

    /** ELECTRONIC / PAPER / FACE */
    private String signType;
    private String signVendor;
    private LocalDateTime signTime;
    private String signFileUrl;
    private String signFlowId;

    /** DRAFT / PENDING_SIGN / SIGNING / EFFECTIVE / RENEWING / EXPIRED / TERMINATED / CANCELLED */
    private String contractStatus;
    private LocalDateTime effectiveTime;
    private LocalDateTime terminateTime;
    private String terminateReason;
    private Long parentContractId;

    private Integer autoGrant;
    private Integer autoExpire;
    private Integer arrearsStop;

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
