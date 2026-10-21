# -*- coding: utf-8 -*-
"""生成复议/异议模块（常量 + 实体 + DTO）"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['biz/constant/AppealBizType.java'] = '''package com.yundao.bp.biz.constant;

/**
 * 申诉/异议的业务类型（对应 {@code bp_biz_appeal.biz_type}）。
 *
 * <p>决定可申诉的对象：申请审批、审核、年度核查、公示、退出。
 */
public enum AppealBizType {

    APPLICATION("申请"),
    REVIEW("审核"),
    ANNUAL_REVIEW("年度核查"),
    PUBLICITY("公示异议"),
    EXIT("退出");

    private final String label;

    AppealBizType(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }
}
'''

FILES['biz/constant/AppealStatus.java'] = '''package com.yundao.bp.biz.constant;

import java.util.Set;

/**
 * 申诉/异议状态（对应 {@code bp_biz_appeal.appeal_status}）。
 *
 * <pre>
 *   SUBMITTED 已提交 → ACCEPTED 已受理 → INVESTIGATING 调查中
 *        │                                   │
 *        │                         ┌─────────┴─────────┐
 *        │                    UPHELD 异议成立    REJECTED 异议不成立
 *        │                    （终态）            （终态）
 *        ├──撤回──> WITHDRAWN（终态）
 *        └──超期──> TIMEOUT（终态；超出 deadline_time 未提出）
 * </pre>
 */
public enum AppealStatus {

    SUBMITTED("已提交", false),
    ACCEPTED("已受理", false),
    INVESTIGATING("调查中", false),
    UPHELD("异议成立", true),
    REJECTED("异议不成立", true),
    WITHDRAWN("已撤回", true),
    TIMEOUT("超期", true);

    private final String label;
    private final boolean terminal;

    AppealStatus(String label, boolean terminal) {
        this.label = label;
        this.terminal = terminal;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return terminal;
    }

    public static Set<AppealStatus> nextOf(AppealStatus from) {
        return switch (from) {
            case SUBMITTED -> Set.of(ACCEPTED, WITHDRAWN, TIMEOUT);
            case ACCEPTED -> Set.of(INVESTIGATING, WITHDRAWN);
            case INVESTIGATING -> Set.of(UPHELD, REJECTED);
            case UPHELD, REJECTED, WITHDRAWN, TIMEOUT -> Set.of();
        };
    }
}
'''

FILES['biz/constant/AppealResultEffect.java'] = '''package com.yundao.bp.biz.constant;

/**
 * 复议结果影响（对应 {@code bp_biz_appeal.result_effect}）。
 *
 * <p>⭐ 这是复议<b>真正产生后果</b>的字段：维持原结论 / 恢复资格 / 取消资格 / 调整标准。
 */
public enum AppealResultEffect {

    RESTORE("恢复资格"),
    CANCEL("取消资格"),
    ADJUST("调整标准"),
    NONE("无影响");

    private final String label;

    AppealResultEffect(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 是否改变了原结论。 */
    public boolean changesOutcome() {
        return this != NONE;
    }
}
'''

FILES['biz/entity/BizAppeal.java'] = '''package com.yundao.bp.biz.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 申诉/异议单。对应 {@code bp_biz_appeal}。
 *
 * <p>保障房的法定救济通道：对审核结论、年审核查、公示内容、退出决定不服时提出。
 */
@Data
@TableName("bp_biz_appeal")
public class BizAppeal {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String appealNo;

    /** APPLICATION / REVIEW / ANNUAL_REVIEW / PUBLICITY / EXIT */
    private String bizType;
    private Long bizId;
    private Long personId;
    private Long orgId;

    /** SUBMIT 申诉 / OBJECTION 公示异议 */
    private String appealType;

    private String appealReason;
    private String appealEvidence;

    /** 申诉截止时间（政策时限） */
    private LocalDateTime deadlineTime;
    private LocalDateTime appealTime;

    private LocalDateTime acceptTime;
    private Long acceptUserId;
    private Long handleUserId;
    private LocalDateTime handleTime;

    private String handleResult;
    private String reviewOpinion;

    /** SUBMITTED / ACCEPTED / INVESTIGATING / UPHELD / REJECTED / WITHDRAWN / TIMEOUT */
    private String appealStatus;

    /** RESTORE / CANCEL / ADJUST / NONE */
    private String resultEffect;
    /** PENDING 待告知 / SENT 已告知 */
    private String notifyStatus;

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

FILES['biz/mapper/BizAppealMapper.java'] = '''package com.yundao.bp.biz.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.biz.entity.BizAppeal;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface BizAppealMapper extends BaseMapper<BizAppeal> {
}
'''

FILES['biz/dto/AppealCreateCmd.java'] = '''package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/**
 * 提出申诉/异议。
 *
 * @param daysFromNow 申诉期限天数（政策时限，如收到告知起 10 个工作日）；为空则不设期限
 */
public record AppealCreateCmd(

        @NotBlank(message = "业务类型不能为空")
        @Pattern(regexp = "APPLICATION|REVIEW|ANNUAL_REVIEW|PUBLICITY|EXIT",
                message = "业务类型不合法")
        String bizType,

        @NotNull(message = "关联业务ID不能为空")
        Long bizId,

        @NotNull(message = "申请人不能为空")
        Long personId,

        Long orgId,

        @NotBlank(message = "申诉类型不能为空")
        @Pattern(regexp = "SUBMIT|OBJECTION", message = "申诉类型不合法")
        String appealType,

        @NotBlank(message = "申诉理由不能为空")
        @Size(max = 2000, message = "理由不能超过 2000 字")
        String appealReason,

        @Size(max = 2000, message = "证据材料不能超过 2000 字")
        String appealEvidence,

        /** 申诉期限天数（工作日近似按自然日计，由业务配置） */
        Integer daysFromNow
) {
}
'''

FILES['biz/dto/AppealDecisionCmd.java'] = '''package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/**
 * 复议决定。
 *
 * @param resultEffect RESTORE 恢复资格 / CANCEL 取消资格 / ADJUST 调整标准 / NONE 无影响
 */
public record AppealDecisionCmd(

        @NotBlank(message = "决定结论不能为空")
        @Pattern(regexp = "UPHELD|REJECTED", message = "决定结论只能是 UPHELD 或 REJECTED")
        String decision,

        @Size(max = 2000, message = "调查核实情况不能超过 2000 字")
        String handleResult,

        @Size(max = 2000, message = "复核意见不能超过 2000 字")
        String reviewOpinion,

        @NotBlank(message = "结果影响不能为空")
        @Pattern(regexp = "RESTORE|CANCEL|ADJUST|NONE", message = "结果影响不合法")
        String resultEffect,

        Long handleUserId
) {
}
'''

FILES['biz/dto/AppealVO.java'] = '''package com.yundao.bp.biz.dto;

import com.yundao.bp.biz.constant.AppealBizType;
import com.yundao.bp.biz.constant.AppealResultEffect;
import com.yundao.bp.biz.constant.AppealStatus;
import com.yundao.bp.biz.entity.BizAppeal;
import java.time.LocalDateTime;

/**
 * 申诉/异议视图。
 */
public record AppealVO(
        Long id,
        String appealNo,
        String bizType,
        String bizTypeLabel,
        Long bizId,
        Long personId,
        Long orgId,
        String appealType,
        String appealReason,
        String appealEvidence,
        LocalDateTime deadlineTime,
        LocalDateTime appealTime,
        /** 派生：是否已超申诉期限 */
        Boolean overdue,
        LocalDateTime acceptTime,
        Long acceptUserId,
        Long handleUserId,
        LocalDateTime handleTime,
        String handleResult,
        String reviewOpinion,
        String appealStatus,
        String appealStatusLabel,
        String resultEffect,
        String resultEffectLabel,
        Boolean changesOutcome,
        String notifyStatus,
        Boolean notified,
        LocalDateTime createTime
) {
    public static AppealVO from(BizAppeal e) {
        if (e == null) {
            return null;
        }
        AppealStatus st;
        try {
            st = AppealStatus.valueOf(e.getAppealStatus());
        } catch (IllegalArgumentException ex) {
            st = AppealStatus.SUBMITTED;
        }
        AppealBizType bt;
        try {
            bt = AppealBizType.valueOf(e.getBizType());
        } catch (IllegalArgumentException ex) {
            bt = AppealBizType.APPLICATION;
        }
        AppealResultEffect re = null;
        if (e.getResultEffect() != null && !e.getResultEffect().isBlank()) {
            try {
                re = AppealResultEffect.valueOf(e.getResultEffect());
            } catch (IllegalArgumentException ignored) {
                re = AppealResultEffect.NONE;
            }
        }
        boolean overdue = e.getDeadlineTime() != null
                && LocalDateTime.now().isAfter(e.getDeadlineTime())
                && st == AppealStatus.TIMEOUT;
        return new AppealVO(e.getId(), e.getAppealNo(), e.getBizType(), bt.label(), e.getBizId(),
                e.getPersonId(), e.getOrgId(), e.getAppealType(), e.getAppealReason(),
                e.getAppealEvidence(), e.getDeadlineTime(), e.getAppealTime(), overdue,
                e.getAcceptTime(), e.getAcceptUserId(), e.getHandleUserId(), e.getHandleTime(),
                e.getHandleResult(), e.getReviewOpinion(), e.getAppealStatus(), st.label(),
                e.getResultEffect(), re == null ? null : re.label(),
                re != null && re.changesOutcome(), e.getNotifyStatus(),
                "SENT".equals(e.getNotifyStatus()), e.getCreateTime());
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
