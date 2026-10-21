# -*- coding: utf-8 -*-
"""生成 biz 业务办理（申请 + 审核）"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['biz/constant/ApplicationStatus.java'] = '''package com.yundao.bp.biz.constant;

import java.util.Set;

/**
 * 申请单状态机（对应 {@code bp_biz_application.application_status}）。
 *
 * <pre>
 *   DRAFT 草稿 ──提交──> SUBMITTED 已提交 ──受理──> ACCEPTED 已受理
 *                                                      │
 *                                                      ↓
 *                              REVIEWING 审核中 ←──┬──┤
 *                                   │            │  │
 *                          需补件 ──┘            │  └──不通过──> REJECTED（终态）
 *                                   ↓            │
 *                            SUPPLEMENT 待补件 ─┘
 *                                   │
 *                          审核通过 ─┴──> APPROVED 已通过（终态，可进入配租）
 * </pre>
 *
 * <p>另有 {@code CANCELLED} 已取消（终态，申请人主动撤回）。
 */
public enum ApplicationStatus {

    DRAFT("草稿", false),
    SUBMITTED("已提交", false),
    ACCEPTED("已受理", false),
    REVIEWING("审核中", false),
    SUPPLEMENT("待补件", false),
    APPROVED("已通过", true),
    REJECTED("不通过", true),
    CANCELLED("已取消", true);

    private final String label;
    private final boolean terminal;

    ApplicationStatus(String label, boolean terminal) {
        this.label = label;
        this.terminal = terminal;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return terminal;
    }

    /** 是否仍在流程中（可做审核动作）。 */
    public boolean isInReview() {
        return this == ACCEPTED || this == REVIEWING || this == SUPPLEMENT;
    }

    public static Set<ApplicationStatus> nextOf(ApplicationStatus from) {
        return switch (from) {
            case DRAFT -> Set.of(SUBMITTED, CANCELLED);
            case SUBMITTED -> Set.of(ACCEPTED, CANCELLED);
            case ACCEPTED -> Set.of(REVIEWING, REJECTED, CANCELLED);
            case REVIEWING -> Set.of(APPROVED, REJECTED, SUPPLEMENT);
            case SUPPLEMENT -> Set.of(REVIEWING, CANCELLED);
            case APPROVED, REJECTED, CANCELLED -> Set.of();
        };
    }
}
'''

FILES['biz/constant/ReviewStage.java'] = '''package com.yundao.bp.biz.constant;

/**
 * 审核阶段（对应 {@code bp_biz_review_record.review_stage}）。
 *
 * <p>保障房审核通常是多级/多部门联审：
 * 受理初审 → 形式审查 → 多部门联审（不动产/民政/社保等）→ 终审。
 */
public enum ReviewStage {

    ACCEPT("受理初审"),
    FORM("形式审查"),
    JOINT("多部门联审"),
    FINAL("终审");

    private final String label;

    ReviewStage(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 按顺序取下一阶段；已是终审则返回 null。 */
    public ReviewStage next() {
        ReviewStage[] all = values();
        int i = ordinal() + 1;
        return i < all.length ? all[i] : null;
    }

    /** 是否最后一阶段（通过即 APPROVED）。 */
    public boolean isLast() {
        return next() == null;
    }
}
'''

FILES['biz/constant/ReviewResult.java'] = '''package com.yundao.bp.biz.constant;

/**
 * 审核结果（对应 {@code bp_biz_review_record.review_result}）。
 */
public enum ReviewResult {

    PASS("通过"),
    REJECT("不通过"),
    SUPPLEMENT("需补件");

    private final String label;

    ReviewResult(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }
}
'''

FILES['biz/entity/BizApplication.java'] = '''package com.yundao.bp.biz.entity;

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
'''

FILES['biz/entity/BizReviewRecord.java'] = '''package com.yundao.bp.biz.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 审核记录（多级/多部门联审）。对应 {@code bp_biz_review_record}。
 */
@Data
@TableName("bp_biz_review_record")
public class BizReviewRecord {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private Long applicationId;

    private Integer reviewRound;
    /** ACCEPT / FORM / JOINT / FINAL */
    private String reviewStage;
    /** REAL_ESTATE / CIVIL / SOCIAL_SECURITY ... */
    private String reviewDept;
    /** API / BATCH / MANUAL */
    private String reviewType;

    private Long reviewUserId;
    private String reviewUserName;
    private LocalDateTime reviewTime;

    /** PASS / REJECT / SUPPLEMENT */
    private String reviewResult;
    /** 核验项明细（JSON） */
    private String checkItems;
    private BigDecimal score;
    private String reviewOpinion;

    private String adapterRequest;
    private String adapterResponse;

    private LocalDateTime createTime;
}
'''

for mapper, entity in (('BizApplicationMapper', 'BizApplication'),
                       ('BizReviewRecordMapper', 'BizReviewRecord')):
    FILES['biz/mapper/%s.java' % mapper] = '''package com.yundao.bp.biz.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.biz.entity.%s;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface %s extends BaseMapper<%s> {
}
''' % (entity, mapper, entity)

FILES['biz/dto/ApplicationCreateCmd.java'] = '''package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import java.math.BigDecimal;

/**
 * 提交保障房申请。
 */
public record ApplicationCreateCmd(

        @NotNull(message = "受理组织不能为空")
        Long orgId,

        @NotNull(message = "申请人员不能为空")
        Long personId,

        @NotBlank(message = "保障类型不能为空")
        @Pattern(regexp = "PUBLIC|AFFORDABLE|TALENT|LOW_RENT", message = "保障类型不合法")
        String securityType,

        @Pattern(regexp = "^$|HOUSE|SUBSIDY", message = "保障方式不合法")
        String securityMode,

        @Pattern(regexp = "^$|ONLINE|OFFLINE|IMPORT", message = "申请渠道不合法")
        String applyChannel,

        @NotNull(message = "家庭人口数不能为空")
        @Min(value = 1, message = "家庭人口数至少为 1")
        Integer familySize,

        String intentDistrict,
        Long intentProject,
        String intentLayout,
        BigDecimal intentAreaMin,
        BigDecimal intentAreaMax,

        BigDecimal declaredIncome,
        BigDecimal declaredIncomeYear,
        BigDecimal familyPropertyAmount,

        @Pattern(regexp = "^$|LAST_YEAR|LAST_12M", message = "收入统计期不合法")
        String incomeCheckPeriod,

        String formData,
        String attachmentUrls,

        /** 是否签署真实性承诺书（保障房必备） */
        Integer complianceCommitFlag,
        /** 是否书面同意核实申报信息 */
        Integer dataShareAgreeFlag,

        String remark
) {
}
'''

FILES['biz/dto/ReviewCmd.java'] = '''package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;

/**
 * 提交审核结果。
 *
 * @param stage        审核阶段 ACCEPT / FORM / JOINT / FINAL
 * @param dept         审核部门（联审时填：REAL_ESTATE / CIVIL / SOCIAL_SECURITY）
 * @param result       PASS / REJECT / SUPPLEMENT
 * @param opinion      审核意见
 * @param checkItems   核验项明细（JSON 字符串）
 * @param supplementDemand 需补件时的要求
 * @param rejectReason 不通过原因
 */
public record ReviewCmd(

        @NotBlank(message = "审核阶段不能为空")
        @Pattern(regexp = "ACCEPT|FORM|JOINT|FINAL", message = "审核阶段不合法")
        String stage,

        String dept,

        @NotBlank(message = "审核结果不能为空")
        @Pattern(regexp = "PASS|REJECT|SUPPLEMENT", message = "审核结果不合法")
        String result,

        String opinion,
        String checkItems,
        String supplementDemand,
        String rejectReason
) {
}
'''

FILES['biz/dto/ApplicationVO.java'] = '''package com.yundao.bp.biz.dto;

import com.yundao.bp.biz.constant.ApplicationStatus;
import com.yundao.bp.biz.entity.BizApplication;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 申请单视图。
 */
public record ApplicationVO(
        Long id,
        String applicationNo,
        Long orgId,
        Long personId,
        String securityType,
        String securityMode,
        String applyChannel,
        LocalDateTime applyTime,
        Integer familySize,
        String intentDistrict,
        String intentLayout,
        String applicationStatus,
        String applicationStatusLabel,
        String currentNode,
        String rejectReason,
        String supplementDemand,
        BigDecimal declaredIncome,
        BigDecimal incomePerCapita,
        Integer complianceCommitFlag,
        Integer dataShareAgreeFlag,
        LocalDateTime acceptTime,
        String remark,
        LocalDateTime createTime
) {
    public static ApplicationVO from(BizApplication e) {
        if (e == null) {
            return null;
        }
        ApplicationStatus st;
        try {
            st = ApplicationStatus.valueOf(e.getApplicationStatus());
        } catch (IllegalArgumentException ex) {
            st = ApplicationStatus.DRAFT;
        }
        return new ApplicationVO(e.getId(), e.getApplicationNo(), e.getOrgId(),
                e.getPersonId(), e.getSecurityType(), e.getSecurityMode(), e.getApplyChannel(),
                e.getApplyTime(), e.getFamilySize(), e.getIntentDistrict(), e.getIntentLayout(),
                e.getApplicationStatus(), st.label(), e.getCurrentNode(), e.getRejectReason(),
                e.getSupplementDemand(), e.getDeclaredIncome(), e.getIncomePerCapita(),
                e.getComplianceCommitFlag(), e.getDataShareAgreeFlag(), e.getAcceptTime(),
                e.getRemark(), e.getCreateTime());
    }
}
'''

count = 0
for rel, content in FILES.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个文件' % count)
