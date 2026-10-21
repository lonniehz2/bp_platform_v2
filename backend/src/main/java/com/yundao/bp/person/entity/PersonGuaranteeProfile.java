package com.yundao.bp.person.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.baomidou.mybatisplus.annotation.TableLogic;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 保障对象专有档案。对应 `bp_person_guarantee_profile`。
 */
@Data
@TableName("bp_person_guarantee_profile")
public class PersonGuaranteeProfile {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private Long personId;
    /** PUBLIC / AFFORDABLE / TALENT / LOW_RENT */
    private String securityType;
    /** 家庭人口数（决定保障面积/补贴） */
    private Integer familySize;
    /** SINGLE / COUPLE / WITH_CHILD / WITH_ELDER / OTHER */
    private String familyType;
    private BigDecimal monthlyIncome;
    /** LOW / LOW_INCOME / MIDDLE_LOW / NORMAL */
    private String incomeLevel;
    private BigDecimal assetDeclare;
    private Integer hasHouse;
    private Integer houseCount;
    private Integer hasVehicle;
    private String socialSecurity;
    /** 优先条件（逗号分隔） */
    private String priorityFlags;
    private BigDecimal priorityScore;
    private String talentLevel;
    private String talentCertNo;
    private LocalDate talentValidTo;
    /** APPLICANT / UNDER_REVIEW / QUALIFIED / IN_RESIDENCE / EXITED */
    private String profileStatus;
    private LocalDate qualifyDate;
    /** 资格有效期至（年审依据） */
    private LocalDate qualifyExpire;
    private LocalDate firstApplyDate;
    private LocalDate lastReviewDate;
    private LocalDate exitDate;
    private String exitReason;
    private String remark;
    private String createBy;
    private LocalDateTime createTime;
    private String updateBy;
    private LocalDateTime updateTime;

    @TableLogic
    private Integer isDeleted;
}
