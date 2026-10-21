# -*- coding: utf-8 -*-
"""生成 fin 补贴标准与发放（第一部分）"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['fin/constant/SubsidyMode.java'] = '''package com.yundao.bp.fin.constant;

/**
 * 补贴方式（对应 {@code bp_fin_subsidy_standard.subsidy_mode}）。
 *
 * <p>⭐ <b>广州"实物配租 + 租赁补贴"双轨</b>的核心：不同人群用不同方式算补贴。
 *
 * <pre>
 *   FIXED   定额     ：每月固定金额（如低保户 800 元/月）
 *   BY_AREA 按面积   ：补贴单价 × 建筑面积（如 20 元/㎡·月）
 *   BY_PERSON按人    ：人均补贴 × 家庭人口（如 300 元/人·月）
 *   RATIO   按租金比例：实际租金 × 比例（如补贴 60% 市场租金）
 * </pre>
 *
 * <p>所有方式算完后统一受 {@code max_amount}（单户月度封顶）约束。
 */
public enum SubsidyMode {

    FIXED("定额"),
    BY_AREA("按面积"),
    BY_PERSON("按人"),
    RATIO("按租金比例");

    private final String label;

    SubsidyMode(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 是否需要面积参与。 */
    public boolean needsArea() {
        return this == BY_AREA;
    }

    /** 是否需要家庭人口参与。 */
    public boolean needsPersonCount() {
        return this == BY_PERSON;
    }

    /** 是否需要月租金参与。 */
    public boolean needsRent() {
        return this == RATIO;
    }
}
'''

FILES['fin/constant/SubsidyStatus.java'] = '''package com.yundao.bp.fin.constant;

import java.util.Set;

/**
 * 补贴发放状态（对应 {@code bp_fin_subsidy_record.record_status}）。
 *
 * <pre>
 *   PENDING 待发放 ──发起──> PAYING 发放中 ──成功──> SUCCESS 已发放（终态）
 *        │                       │
 *        │                    失败/退回
 *        │                       ↓
 *        │                  FAILED 发放失败（可重试回 PAYING）
 *        └──────────────────> RETURNED 已退回（终态）
 * </pre>
 */
public enum SubsidyStatus {

    PENDING("待发放"),
    PAYING("发放中"),
    SUCCESS("已发放"),
    FAILED("发放失败"),
    RETURNED("已退回");

    private final String label;

    SubsidyStatus(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return this == SUCCESS || this == RETURNED;
    }

    public static Set<SubsidyStatus> nextOf(SubsidyStatus from) {
        return switch (from) {
            case PENDING -> Set.of(PAYING, RETURNED);
            case PAYING -> Set.of(SUCCESS, FAILED, RETURNED);
            case FAILED -> Set.of(PAYING, RETURNED);
            case SUCCESS, RETURNED -> Set.of();
        };
    }
}
'''

FILES['fin/entity/FinSubsidyStandard.java'] = '''package com.yundao.bp.fin.entity;

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
 * 补贴标准。对应 {@code bp_fin_subsidy_standard}。
 */
@Data
@TableName("bp_fin_subsidy_standard")
public class FinSubsidyStandard {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String standardCode;
    private String standardName;

    /** PUBLIC / AFFORDABLE / TALENT / LOW_RENT */
    private String securityType;

    private Long orgId;
    /** 适用收入档位 */
    private String incomeLevel;
    /** 适用家庭类型 */
    private String familyType;
    /** 适用人才层次 */
    private String talentLevel;

    /** FIXED / BY_AREA / BY_PERSON / RATIO */
    private String subsidyMode;
    /** 补贴值（金额/单价/比例） */
    private BigDecimal subsidyValue;
    /** 单户月度封顶 */
    private BigDecimal maxAmount;

    private LocalDate effectiveStart;
    private LocalDate effectiveEnd;

    /** ENABLED / DISABLED */
    private String status;

    @TableLogic
    private Integer isDeleted;

    @TableField(fill = FieldFill.INSERT)
    private String createBy;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
'''

FILES['fin/entity/FinSubsidyRecord.java'] = '''package com.yundao.bp.fin.entity;

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
 * 补贴发放记录。对应 {@code bp_fin_subsidy_record}。
 */
@Data
@TableName("bp_fin_subsidy_record")
public class FinSubsidyRecord {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String recordNo;

    private Long standardId;
    private Long contractId;
    private Long personId;
    private String personName;
    private Long orgId;

    /** 补贴期间，如 2026-10 */
    private String subsidyPeriod;

    /** 应发金额 */
    private BigDecimal subsidyAmount;
    /** 实发金额 */
    private BigDecimal paidAmount;

    /** FINANCE / BANK / OFFSET_RENT */
    private String payMode;
    private String bankAccount;

    /** PENDING / PAYING / SUCCESS / FAILED / RETURNED */
    private String recordStatus;
    private String financeBatchNo;
    private String failReason;
    private LocalDate issueDate;

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

for mapper, entity in (('FinSubsidyStandardMapper', 'FinSubsidyStandard'),
                       ('FinSubsidyRecordMapper', 'FinSubsidyRecord')):
    FILES['fin/mapper/%s.java' % mapper] = '''package com.yundao.bp.fin.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.fin.entity.%s;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface %s extends BaseMapper<%s> {
}
''' % (entity, mapper, entity)

FILES['fin/dto/SubsidyStandardCreateCmd.java'] = '''package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 创建补贴标准。
 *
 * <p>补贴值含义随 {@code subsidyMode} 变化：
 * <ul>
 *   <li>FIXED → 每月金额（元/月）</li>
 *   <li>BY_AREA → 单价（元/㎡·月）</li>
 *   <li>BY_PERSON → 人均（元/人·月）</li>
 *   <li>RATIO → 比例（0~1，如 0.6 表示补贴 60%）</li>
 * </ul>
 */
public record SubsidyStandardCreateCmd(

        @NotBlank(message = "标准编码不能为空")
        @Size(max = 64, message = "编码不能超过 64 字符")
        String standardCode,

        @NotBlank(message = "标准名称不能为空")
        @Size(max = 128, message = "名称不能超过 128 字符")
        String standardName,

        @NotBlank(message = "保障类型不能为空")
        @Pattern(regexp = "PUBLIC|AFFORDABLE|TALENT|LOW_RENT", message = "保障类型不合法")
        String securityType,

        Long orgId,
        String incomeLevel,
        String familyType,
        String talentLevel,

        @NotBlank(message = "补贴方式不能为空")
        @Pattern(regexp = "FIXED|BY_AREA|BY_PERSON|RATIO", message = "补贴方式不合法")
        String subsidyMode,

        @NotNull(message = "补贴值不能为空")
        @DecimalMin(value = "0", message = "补贴值不能为负")
        BigDecimal subsidyValue,

        @DecimalMin(value = "0", message = "封顶金额不能为负")
        BigDecimal maxAmount,

        LocalDate effectiveStart,
        LocalDate effectiveEnd
) {
}
'''

FILES['fin/dto/SubsidyGrantCmd.java'] = '''package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;

/**
 * 发放补贴（单户单期）。
 *
 * <p>金额由服务端按标准计算，不信任前端传入的金额。
 */
public record SubsidyGrantCmd(

        @NotNull(message = "合同不能为空")
        Long contractId,

        @NotNull(message = "受益人不能为空")
        Long personId,

        @NotBlank(message = "补贴期间不能为空")
        @Pattern(regexp = "^\\\\d{4}-\\\\d{2}$", message = "补贴期间格式应为 YYYY-MM")
        String subsidyPeriod,

        /** 可选：指定标准；不传则按保障类型/组织自动匹配 */
        Long standardId,

        @Pattern(regexp = "^$|FINANCE|BANK|OFFSET_RENT", message = "发放方式不合法")
        String payMode,

        String bankAccount
) {
}
'''

FILES['fin/dto/SubsidyStandardVO.java'] = '''package com.yundao.bp.fin.dto;

import com.yundao.bp.fin.constant.SubsidyMode;
import com.yundao.bp.fin.entity.FinSubsidyStandard;
import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 补贴标准视图。
 */
public record SubsidyStandardVO(
        Long id,
        String standardCode,
        String standardName,
        String securityType,
        Long orgId,
        String incomeLevel,
        String familyType,
        String talentLevel,
        String subsidyMode,
        String subsidyModeLabel,
        BigDecimal subsidyValue,
        BigDecimal maxAmount,
        LocalDate effectiveStart,
        LocalDate effectiveEnd,
        String status
) {
    public static SubsidyStandardVO from(FinSubsidyStandard e) {
        if (e == null) {
            return null;
        }
        SubsidyMode m;
        try {
            m = SubsidyMode.valueOf(e.getSubsidyMode());
        } catch (IllegalArgumentException ex) {
            m = SubsidyMode.FIXED;
        }
        return new SubsidyStandardVO(e.getId(), e.getStandardCode(), e.getStandardName(),
                e.getSecurityType(), e.getOrgId(), e.getIncomeLevel(), e.getFamilyType(),
                e.getTalentLevel(), e.getSubsidyMode(), m.label(), e.getSubsidyValue(),
                e.getMaxAmount(), e.getEffectiveStart(), e.getEffectiveEnd(), e.getStatus());
    }
}
'''

FILES['fin/dto/SubsidyRecordVO.java'] = '''package com.yundao.bp.fin.dto;

import com.yundao.bp.fin.constant.SubsidyStatus;
import com.yundao.bp.fin.entity.FinSubsidyRecord;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 补贴发放记录视图。
 */
public record SubsidyRecordVO(
        Long id,
        String recordNo,
        Long standardId,
        Long contractId,
        Long personId,
        String personName,
        Long orgId,
        String subsidyPeriod,
        BigDecimal subsidyAmount,
        BigDecimal paidAmount,
        String payMode,
        String recordStatus,
        String recordStatusLabel,
        String financeBatchNo,
        String failReason,
        LocalDate issueDate,
        LocalDateTime createTime
) {
    public static SubsidyRecordVO from(FinSubsidyRecord e) {
        if (e == null) {
            return null;
        }
        SubsidyStatus st;
        try {
            st = SubsidyStatus.valueOf(e.getRecordStatus());
        } catch (IllegalArgumentException ex) {
            st = SubsidyStatus.PENDING;
        }
        return new SubsidyRecordVO(e.getId(), e.getRecordNo(), e.getStandardId(),
                e.getContractId(), e.getPersonId(), e.getPersonName(), e.getOrgId(),
                e.getSubsidyPeriod(), e.getSubsidyAmount(), e.getPaidAmount(), e.getPayMode(),
                e.getRecordStatus(), st.label(), e.getFinanceBatchNo(), e.getFailReason(),
                e.getIssueDate(), e.getCreateTime());
    }
}
'''

FILES['fin/dto/SubsidyCalcCmd.java'] = '''package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;

/**
 * 补贴试算（不落库）。
 */
public record SubsidyCalcCmd(

        @NotNull(message = "合同不能为空")
        Long contractId,

        Long standardId,

        /** 面积（BY_AREA 用；不传取合同/房源面积） */
        BigDecimal area,

        /** 家庭人口（BY_PERSON 用） */
        Integer personCount,

        /** 月租金（RATIO 用；不传取合同月租金） */
        BigDecimal monthlyRent
) {
}
'''

count = 0
for rel, content in FILES.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个文件' % count)
