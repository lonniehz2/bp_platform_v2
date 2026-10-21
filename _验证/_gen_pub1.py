# -*- coding: utf-8 -*-
"""生成 公示 + 年审 模块（常量 + 实体 + DTO）"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

# ==================== 常量 ====================
FILES['biz/constant/PublicityType.java'] = '''package com.yundao.bp.biz.constant;

/**
 * 公示类型（对应 {@code bp_biz_publicity.publicity_type}）。
 */
public enum PublicityType {

    QUALIFY("资格公示"),
    ALLOCATION("配租公示"),
    EXIT("退出公示");

    private final String label;

    PublicityType(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }
}
'''

FILES['biz/constant/PublicityStatus.java'] = '''package com.yundao.bp.biz.constant;

import java.util.Set;

/**
 * 公示状态（对应 {@code bp_biz_publicity.publicity_status}）。
 *
 * <pre>
 *   DRAFT 草稿 → PUBLISHED 已发布 → CLOSED 已结束（终态）
 * </pre>
 *
 * <p>⭐ <b>合规要求（决策 D23）</b>：配租结果必须公示，
 * 且公示期不少于 {@code 7} 个自然日；配租公示<b>未结束不得签约</b>。
 */
public enum PublicityStatus {

    DRAFT("草稿", false),
    PUBLISHED("已发布", false),
    CLOSED("已结束", true);

    private final String label;
    private final boolean terminal;

    PublicityStatus(String label, boolean terminal) {
        this.label = label;
        this.terminal = terminal;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return terminal;
    }

    public static Set<PublicityStatus> nextOf(PublicityStatus from) {
        return switch (from) {
            case DRAFT -> Set.of(PUBLISHED);
            case PUBLISHED -> Set.of(CLOSED);
            case CLOSED -> Set.of();
        };
    }
}
'''

FILES['biz/constant/ReviewStatus.java'] = '''package com.yundao.bp.biz.constant;

import java.util.Set;

/**
 * 年审（复核）状态（对应 {@code bp_biz_annual_review.review_status}）。
 *
 * <pre>
 *   PENDING 待复核 → REVIEWING 复核中 → DONE 已完成（终态）
 *   超期未复核 → OVERDUE 已逾期（可继续复核 → DONE）
 * </pre>
 */
public enum ReviewStatus {

    PENDING("待复核", false),
    REVIEWING("复核中", false),
    DONE("已完成", true),
    OVERDUE("已逾期", false);

    private final String label;
    private final boolean terminal;

    ReviewStatus(String label, boolean terminal) {
        this.label = label;
        this.terminal = terminal;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return terminal;
    }

    public static Set<ReviewStatus> nextOf(ReviewStatus from) {
        return switch (from) {
            case PENDING -> Set.of(REVIEWING, OVERDUE);
            case REVIEWING -> Set.of(DONE, OVERDUE);
            case OVERDUE -> Set.of(REVIEWING, DONE);
            case DONE -> Set.of();
        };
    }
}
'''

FILES['biz/constant/ReviewResult.java'] = '''package com.yundao.bp.biz.constant;

/**
 * 复核结果（对应 {@code bp_biz_annual_review.review_result}）。
 */
public enum ReviewResult {

    KEEP("保留资格"),
    ADJUST("调整（租金/房源）"),
    EXIT("退出"),
    PENDING("待定");

    private final String label;

    ReviewResult(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 是否需要后续处置（调整或退出）。 */
    public boolean needsAction() {
        return this == ADJUST || this == EXIT;
    }
}
'''

# ==================== 实体 ====================
FILES['biz/entity/BizPublicity.java'] = '''package com.yundao.bp.biz.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 公示。对应 {@code bp_biz_publicity}。
 */
@Data
@TableName("bp_biz_publicity")
public class BizPublicity {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String publicityNo;

    /** QUALIFY / ALLOCATION / EXIT */
    private String publicityType;
    private Long orgId;

    private String title;
    private String content;
    private LocalDate startDate;
    private LocalDate endDate;
    private String attachmentUrl;

    /** DRAFT / PUBLISHED / CLOSED */
    private String publicityStatus;

    @TableField(fill = FieldFill.INSERT)
    private String createBy;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
'''

FILES['biz/entity/BizAnnualReview.java'] = '''package com.yundao.bp.biz.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 年审（复核）。对应 {@code bp_biz_annual_review}。
 */
@Data
@TableName("bp_biz_annual_review")
public class BizAnnualReview {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String reviewNo;

    private Long personId;
    private Long contractId;
    private Long houseId;

    /** 复核年度，如 2026 */
    private String reviewYear;
    private String reviewBatch;

    /** ANNUAL / DYNAMIC / SPECIAL */
    private String reviewType;
    private String triggerReason;
    /** 核验结果明细 JSON */
    private String checkResult;

    /** KEEP / ADJUST / EXIT / PENDING */
    private String reviewResult;
    private String adjustContent;

    /** PENDING / REVIEWING / DONE / OVERDUE */
    private String reviewStatus;
    private LocalDate reviewDate;
    private LocalDate nextReviewDate;
    private Long reviewUserId;

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

for mapper, entity in (('BizPublicityMapper', 'BizPublicity'),
                       ('BizAnnualReviewMapper', 'BizAnnualReview')):
    FILES['biz/mapper/%s.java' % mapper] = '''package com.yundao.bp.biz.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.biz.entity.%s;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface %s extends BaseMapper<%s> {
}
''' % (entity, mapper, entity)

# ==================== DTO ====================
FILES['biz/dto/PublicityCreateCmd.java'] = '''package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import java.time.LocalDate;

/**
 * 创建公示。
 *
 * <p>⭐ 合规：配租公示（ALLOCATION）公示期<b>不得少于 7 个自然日</b>。
 */
public record PublicityCreateCmd(

        @NotBlank(message = "公示类型不能为空")
        @Pattern(regexp = "QUALIFY|ALLOCATION|EXIT", message = "公示类型不合法")
        String publicityType,

        Long orgId,

        @NotBlank(message = "标题不能为空")
        String title,

        String content,

        @NotNull(message = "公示开始日期不能为空")
        LocalDate startDate,

        @NotNull(message = "公示结束日期不能为空")
        LocalDate endDate,

        String attachmentUrl
) {
}
'''

FILES['biz/dto/ReviewCreateCmd.java'] = '''package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;

/**
 * 创建复核（年审/动态核查）。
 */
public record ReviewCreateCmd(

        @NotNull(message = "人员不能为空")
        Long personId,

        Long contractId,
        Long houseId,

        @NotBlank(message = "复核年度不能为空")
        @Pattern(regexp = "^\\\\d{4}$", message = "复核年度格式应为 YYYY")
        String reviewYear,

        String reviewBatch,

        @NotBlank(message = "复核类型不能为空")
        @Pattern(regexp = "ANNUAL|DYNAMIC|SPECIAL", message = "复核类型不合法")
        String reviewType,

        String triggerReason
) {
}
'''

FILES['biz/dto/ReviewFinishCmd.java'] = '''package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;

/**
 * 完成复核。
 *
 * @param checkResult   核验明细 JSON（收入/房产/人口变化等）
 * @param adjustContent 调整内容（结果 ADJUST 时）
 */
public record ReviewFinishCmd(

        @NotBlank(message = "复核结果不能为空")
        @Pattern(regexp = "KEEP|ADJUST|EXIT|PENDING", message = "复核结果不合法")
        String reviewResult,

        String checkResult,
        String adjustContent,
        Long reviewUserId,

        /** 下次复核日期；为空则默认次年同日 */
        String nextReviewDate
) {
}
'''

FILES['biz/dto/PublicityVO.java'] = '''package com.yundao.bp.biz.dto;

import com.yundao.bp.biz.constant.PublicityStatus;
import com.yundao.bp.biz.constant.PublicityType;
import com.yundao.bp.biz.entity.BizPublicity;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;

/**
 * 公示视图。
 */
public record PublicityVO(
        Long id,
        String publicityNo,
        String publicityType,
        String publicityTypeLabel,
        Long orgId,
        String title,
        String content,
        LocalDate startDate,
        LocalDate endDate,
        /** 公示天数 */
        Long durationDays,
        String attachmentUrl,
        String publicityStatus,
        String publicityStatusLabel,
        /** 派生：公示期是否已满（≥7 天且已到结束日） */
        Boolean periodMet,
        /** 派生：是否正在进行中 */
        Boolean ongoing,
        LocalDateTime createTime
) {
    public static PublicityVO from(BizPublicity e) {
        if (e == null) {
            return null;
        }
        PublicityStatus st;
        try {
            st = PublicityStatus.valueOf(e.getPublicityStatus());
        } catch (IllegalArgumentException ex) {
            st = PublicityStatus.DRAFT;
        }
        PublicityType tp;
        try {
            tp = PublicityType.valueOf(e.getPublicityType());
        } catch (IllegalArgumentException ex) {
            tp = PublicityType.QUALIFY;
        }
        long days = 0;
        if (e.getStartDate() != null && e.getEndDate() != null) {
            days = ChronoUnit.DAYS.between(e.getStartDate(), e.getEndDate()) + 1;
        }
        LocalDate today = LocalDate.now();
        boolean met = days >= 7 && e.getEndDate() != null && !today.isBefore(e.getEndDate());
        boolean ongoing = st == PublicityStatus.PUBLISHED && e.getStartDate() != null
                && e.getEndDate() != null
                && !today.isBefore(e.getStartDate()) && !today.isAfter(e.getEndDate());
        return new PublicityVO(e.getId(), e.getPublicityNo(), e.getPublicityType(), tp.label(),
                e.getOrgId(), e.getTitle(), e.getContent(), e.getStartDate(), e.getEndDate(),
                days, e.getAttachmentUrl(), e.getPublicityStatus(), st.label(), met, ongoing,
                e.getCreateTime());
    }
}
'''

FILES['biz/dto/ReviewVO.java'] = '''package com.yundao.bp.biz.dto;

import com.yundao.bp.biz.constant.ReviewResult;
import com.yundao.bp.biz.constant.ReviewStatus;
import com.yundao.bp.biz.entity.BizAnnualReview;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 年审（复核）视图。
 */
public record ReviewVO(
        Long id,
        String reviewNo,
        Long personId,
        Long contractId,
        Long houseId,
        String reviewYear,
        String reviewBatch,
        String reviewType,
        String triggerReason,
        String checkResult,
        String reviewResult,
        String reviewResultLabel,
        String adjustContent,
        String reviewStatus,
        String reviewStatusLabel,
        LocalDate reviewDate,
        LocalDate nextReviewDate,
        Long reviewUserId,
        LocalDateTime createTime
) {
    public static ReviewVO from(BizAnnualReview e) {
        if (e == null) {
            return null;
        }
        ReviewStatus st;
        try {
            st = ReviewStatus.valueOf(e.getReviewStatus());
        } catch (IllegalArgumentException ex) {
            st = ReviewStatus.PENDING;
        }
        String rl = null;
        if (e.getReviewResult() != null && !e.getReviewResult().isBlank()) {
            try {
                rl = ReviewResult.valueOf(e.getReviewResult()).label();
            } catch (IllegalArgumentException ex) {
                rl = e.getReviewResult();
            }
        }
        return new ReviewVO(e.getId(), e.getReviewNo(), e.getPersonId(), e.getContractId(),
                e.getHouseId(), e.getReviewYear(), e.getReviewBatch(), e.getReviewType(),
                e.getTriggerReason(), e.getCheckResult(), e.getReviewResult(), rl,
                e.getAdjustContent(), e.getReviewStatus(), st.label(), e.getReviewDate(),
                e.getNextReviewDate(), e.getReviewUserId(), e.getCreateTime());
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
