package com.yundao.bp.biz.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 申请单（受理）。对应 {@code bp_biz_application}。
 */
@Data
@TableName("bp_biz_application")
public class BizApplication {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String applicationNo;

    private Long orgId;
    private Long personId;

    /** PUBLIC 公租 / AFFORDABLE 保租 / TALENT 人才 ... */
    private String securityType;
    /** ONLINE / OFFLINE / ... */
    private String applyChannel;
    private LocalDateTime applyTime;
    private Integer familySize;

    private String intentDistrict;
    private Long intentProject;
    private String intentLayout;
    private BigDecimal intentAreaMin;
    private BigDecimal intentAreaMax;

    /** 动态表单数据（JSON） */
    private String formData;
    private String attachmentUrls;

    /** DRAFT / SUBMITTED / ACCEPTED / REVIEWING / SUPPLEMENT / APPROVED / REJECTED / CANCELLED */
    private String applicationStatus;
    private LocalDateTime acceptTime;
    private Long acceptUserId;
    private String currentNode;
    private String rejectReason;
    private String supplementDemand;

    /** HOUSE 实物配租 / SUBSIDY 租赁补贴 */
    private String securityMode;

    private BigDecimal declaredIncome;
    private BigDecimal declaredIncomeYear;
    /** 人均月收入（计算值，用于分档判定） */
    private BigDecimal incomePerCapita;
    private BigDecimal familyPropertyAmount;
    private String incomeCheckPeriod;

    private String hukouType;
    private String hukouAddress;
    private Long serviceAddressId;

    private Integer complianceCommitFlag;
    private Integer dataShareAgreeFlag;

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
