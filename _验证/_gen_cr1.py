# -*- coding: utf-8 -*-
"""生成信用记录模块（常量 + 实体 + DTO）"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['biz/constant/ViolationType.java'] = '''package com.yundao.bp.biz.constant;

/**
 * 违规类型（对应 {@code bp_biz_credit_record.violation_type}）。
 */
public enum ViolationType {

    FALSE_INFO("提供虚假信息"),
    SUBLEASE("转租出借"),
    STRUCTURE("破坏结构"),
    CHANGE_USE("改变用途"),
    VACANT("长期空置"),
    ILLEGAL("从事违法活动"),
    ARREARS("恶意欠租"),
    OTHER("其他");

    private final String label;

    ViolationType(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 是否属于严重违规（默认需限制申请年限）。 */
    public boolean severe() {
        return this == FALSE_INFO || this == SUBLEASE || this == ILLEGAL
                || this == STRUCTURE;
    }
}
'''

FILES['biz/constant/SanctionType.java'] = '''package com.yundao.bp.biz.constant;

/**
 * 惩戒措施（对应 {@code bp_biz_credit_record.sanction_type}）。
 */
public enum SanctionType {

    TERMINATE("终止资格"),
    BAN_APPLY("限制申请"),
    CREDIT_PLATFORM("推送信用平台"),
    FINE("罚款"),
    OTHER("其他");

    private final String label;

    SanctionType(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 是否需计算限制申请年限。 */
    public boolean needsBanYears() {
        return this == BAN_APPLY;
    }
}
'''

FILES['biz/constant/CreditStatus.java'] = '''package com.yundao.bp.biz.constant;

import java.util.Set;

/**
 * 信用记录状态（对应 {@code bp_biz_credit_record.status}）。
 *
 * <pre>
 *   EFFECTIVE 生效中 ──期满──> EXPIRED 已解除（终态）
 *        └──复议/纠错撤销──> REVOKED 已撤销（终态）
 * </pre>
 */
public enum CreditStatus {

    EFFECTIVE("生效中"),
    EXPIRED("已解除"),
    REVOKED("已撤销");

    private final String label;

    CreditStatus(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return this != EFFECTIVE;
    }

    public static Set<CreditStatus> nextOf(CreditStatus from) {
        return switch (from) {
            case EFFECTIVE -> Set.of(EXPIRED, REVOKED);
            case EXPIRED, REVOKED -> Set.of();
        };
    }
}
'''

FILES['biz/entity/BizCreditRecord.java'] = '''package com.yundao.bp.biz.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 信用惩戒记录。对应 {@code bp_biz_credit_record}。
 *
 * <p>⭐ 保障房「失信惩戒」是核心管理抓手：转租出借、提供虚假信息等行为
 * 会被记录并<b>限制再申请年限</b>（政策常见 5 年）。
 */
@Data
@TableName("bp_biz_credit_record")
public class BizCreditRecord {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String recordNo;

    private Long personId;

    /** EXIT / CONTRACT / APPLICATION */
    private String bizType;
    private Long bizId;

    /** FALSE_INFO / SUBLEASE / STRUCTURE / CHANGE_USE / VACANT / ILLEGAL / ARREARS / OTHER */
    private String violationType;
    private String violationDesc;
    private String evidenceUrl;

    /** TERMINATE / BAN_APPLY / CREDIT_PLATFORM / FINE / OTHER */
    private String sanctionType;
    /** 限制申请年限 */
    private Integer banYears;
    private LocalDate banStartDate;
    private LocalDate banEndDate;

    private String pushPlatform;
    /** PENDING / PUSHED / FAILED / NONE */
    private String pushStatus;
    private LocalDateTime pushTime;

    private Long decideOrgId;
    private Long decideUserId;
    private LocalDateTime decideTime;
    private String legalDocNo;

    /** EFFECTIVE / EXPIRED / REVOKED */
    private String status;
    private String remark;

    @TableField(fill = FieldFill.INSERT)
    private String createBy;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private String updateBy;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;

    @TableLogic
    private Integer isDeleted;
}
'''

FILES['biz/mapper/BizCreditRecordMapper.java'] = '''package com.yundao.bp.biz.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.biz.entity.BizCreditRecord;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface BizCreditRecordMapper extends BaseMapper<BizCreditRecord> {
}
'''

FILES['biz/dto/CreditCreateCmd.java'] = '''package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/**
 * 记入信用惩戒。
 *
 * @param banYears 限制申请年限；{@code sanctionType=BAN_APPLY} 时必填（政策常见 5 年）
 */
public record CreditCreateCmd(

        @NotNull(message = "人员不能为空")
        Long personId,

        @Pattern(regexp = "^$|EXIT|CONTRACT|APPLICATION", message = "业务类型不合法")
        String bizType,
        Long bizId,

        @NotBlank(message = "违规类型不能为空")
        @Pattern(regexp = "FALSE_INFO|SUBLEASE|STRUCTURE|CHANGE_USE|VACANT|ILLEGAL|ARREARS|OTHER",
                message = "违规类型不合法")
        String violationType,

        @Size(max = 2000, message = "违规描述不能超过 2000 字")
        String violationDesc,

        String evidenceUrl,

        @NotBlank(message = "惩戒措施不能为空")
        @Pattern(regexp = "TERMINATE|BAN_APPLY|CREDIT_PLATFORM|FINE|OTHER",
                message = "惩戒措施不合法")
        String sanctionType,

        Integer banYears,

        Long decideOrgId,
        Long decideUserId,
        String legalDocNo,

        /** 是否推送信用平台（推送状态初始为 PENDING） */
        Boolean pushToPlatform,
        String pushPlatform,

        String remark
) {
}
'''

FILES['biz/dto/CreditVO.java'] = '''package com.yundao.bp.biz.dto;

import com.yundao.bp.biz.constant.CreditStatus;
import com.yundao.bp.biz.constant.SanctionType;
import com.yundao.bp.biz.constant.ViolationType;
import com.yundao.bp.biz.entity.BizCreditRecord;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 信用惩戒记录视图。
 */
public record CreditVO(
        Long id,
        String recordNo,
        Long personId,
        String bizType,
        Long bizId,
        String violationType,
        String violationTypeLabel,
        String violationDesc,
        String evidenceUrl,
        String sanctionType,
        String sanctionTypeLabel,
        Integer banYears,
        LocalDate banStartDate,
        LocalDate banEndDate,
        /** 派生：当前是否处于限制申请期内 */
        Boolean underBan,
        String pushPlatform,
        String pushStatus,
        Boolean pushed,
        LocalDateTime pushTime,
        Long decideOrgId,
        Long decideUserId,
        LocalDateTime decideTime,
        String legalDocNo,
        String status,
        String statusLabel,
        String remark,
        LocalDateTime createTime
) {
    public static CreditVO from(BizCreditRecord e) {
        if (e == null) {
            return null;
        }
        CreditStatus st;
        try {
            st = CreditStatus.valueOf(e.getStatus());
        } catch (IllegalArgumentException ex) {
            st = CreditStatus.EFFECTIVE;
        }
        ViolationType vt;
        try {
            vt = ViolationType.valueOf(e.getViolationType());
        } catch (IllegalArgumentException ex) {
            vt = ViolationType.OTHER;
        }
        SanctionType sa;
        try {
            sa = SanctionType.valueOf(e.getSanctionType());
        } catch (IllegalArgumentException ex) {
            sa = SanctionType.OTHER;
        }
        LocalDate today = LocalDate.now();
        boolean underBan = st == CreditStatus.EFFECTIVE
                && e.getBanEndDate() != null
                && !today.isAfter(e.getBanEndDate())
                && (e.getBanStartDate() == null || !today.isBefore(e.getBanStartDate()));
        return new CreditVO(e.getId(), e.getRecordNo(), e.getPersonId(), e.getBizType(),
                e.getBizId(), e.getViolationType(), vt.label(), e.getViolationDesc(),
                e.getEvidenceUrl(), e.getSanctionType(), sa.label(), e.getBanYears(),
                e.getBanStartDate(), e.getBanEndDate(), underBan, e.getPushPlatform(),
                e.getPushStatus(), "PUSHED".equals(e.getPushStatus()), e.getPushTime(),
                e.getDecideOrgId(), e.getDecideUserId(), e.getDecideTime(), e.getLegalDocNo(),
                e.getStatus(), st.label(), e.getRemark(), e.getCreateTime());
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
