# -*- coding: utf-8 -*-
"""生成 complaint + house_visit（第 1 部分：常量/实体/Mapper/DTO）"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

# ==================== 投诉建议 ====================
FILES['ops/constant/ComplaintStatus.java'] = '''package com.yundao.bp.ops.constant;

import java.util.Set;

/**
 * 投诉/建议处理状态（对应 {@code bp_ops_complaint.handle_status}）。
 *
 * <pre>
 *   PENDING 待处理 → HANDLING 处理中 → HANDLED 已处理 → CLOSED 已归档
 * </pre>
 */
public enum ComplaintStatus {

    PENDING("待处理"),
    HANDLING("处理中"),
    HANDLED("已处理"),
    CLOSED("已归档");

    private final String label;

    ComplaintStatus(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return this == CLOSED;
    }

    public static Set<ComplaintStatus> nextOf(ComplaintStatus from) {
        return switch (from) {
            case PENDING -> Set.of(HANDLING, HANDLED);
            case HANDLING -> Set.of(HANDLED);
            case HANDLED -> Set.of(CLOSED);
            case CLOSED -> Set.of();
        };
    }
}
'''

FILES['ops/entity/OpsComplaint.java'] = '''package com.yundao.bp.ops.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 投诉建议。对应 {@code bp_ops_complaint}。
 */
@Data
@TableName("bp_ops_complaint")
public class OpsComplaint {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String complaintNo;

    /** COMPLAINT 投诉 / SUGGEST 建议 / CONSULT 咨询 / PRAISE 表扬 */
    private String complaintType;
    /** MINIAPP / APP / PHONE / WALKIN / OTHER */
    private String source;

    private Long orgId;
    private Long personId;
    private String submitterName;
    private String submitterPhone;

    private String title;
    private String content;
    private String images;

    private Long workorderId;

    /** PENDING / HANDLING / HANDLED / CLOSED */
    private String handleStatus;
    private Long handleUserId;
    private LocalDateTime handleTime;
    private String handleResult;
    /** 满意度 1-5 */
    private Integer satisfaction;

    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
'''

FILES['ops/mapper/OpsComplaintMapper.java'] = '''package com.yundao.bp.ops.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.ops.entity.OpsComplaint;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface OpsComplaintMapper extends BaseMapper<OpsComplaint> {
}
'''

FILES['ops/dto/ComplaintCreateCmd.java'] = '''package com.yundao.bp.ops.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/**
 * 提交投诉/建议/咨询/表扬。
 */
public record ComplaintCreateCmd(

        @NotBlank(message = "类型不能为空")
        @Pattern(regexp = "COMPLAINT|SUGGEST|CONSULT|PRAISE", message = "类型不合法")
        String complaintType,

        @Pattern(regexp = "^$|MINIAPP|APP|PHONE|WALKIN|OTHER", message = "来源不合法")
        String source,

        @NotBlank(message = "标题不能为空")
        @Size(max = 255, message = "标题不能超过 255 字符")
        String title,

        @Size(max = 2000, message = "内容不能超过 2000 字符")
        String content,

        String images,
        Long orgId,
        Long personId,
        String submitterName,
        String submitterPhone
) {
}
'''

FILES['ops/dto/ComplaintVO.java'] = '''package com.yundao.bp.ops.dto;

import com.yundao.bp.ops.constant.ComplaintStatus;
import com.yundao.bp.ops.entity.OpsComplaint;
import java.time.LocalDateTime;

/**
 * 投诉建议视图。
 */
public record ComplaintVO(
        Long id,
        String complaintNo,
        String complaintType,
        String source,
        String title,
        String content,
        String images,
        Long orgId,
        Long personId,
        String submitterName,
        String submitterPhone,
        String handleStatus,
        String handleStatusLabel,
        Long handleUserId,
        LocalDateTime handleTime,
        String handleResult,
        Integer satisfaction,
        Long workorderId,
        /** 派生：是否超时未处理（投诉类 48 小时未处理） */
        Boolean overdue,
        LocalDateTime createTime
) {
    public static ComplaintVO from(OpsComplaint e) {
        if (e == null) {
            return null;
        }
        ComplaintStatus st;
        try {
            st = ComplaintStatus.valueOf(e.getHandleStatus());
        } catch (IllegalArgumentException ex) {
            st = ComplaintStatus.PENDING;
        }
        boolean overdue = false;
        if (!st.isTerminal() && e.getCreateTime() != null
                && "COMPLAINT".equals(e.getComplaintType())) {
            overdue = LocalDateTime.now().isAfter(e.getCreateTime().plusHours(48));
        }
        return new ComplaintVO(e.getId(), e.getComplaintNo(), e.getComplaintType(), e.getSource(),
                e.getTitle(), e.getContent(), e.getImages(), e.getOrgId(), e.getPersonId(),
                e.getSubmitterName(), e.getSubmitterPhone(), e.getHandleStatus(), st.label(),
                e.getHandleUserId(), e.getHandleTime(), e.getHandleResult(), e.getSatisfaction(),
                e.getWorkorderId(), overdue, e.getCreateTime());
    }
}
'''

# ==================== 巡房走访 ====================
FILES['ops/constant/VisitStatus.java'] = '''package com.yundao.bp.ops.constant;

import java.util.Set;

/**
 * 走访状态（对应 {@code bp_ops_house_visit.visit_status}）。
 *
 * <pre>
 *   PENDING 待走访 ──完成──> DONE 已完成
 *      ├──拒访──> REFUSED
 *      ├──无人──> ABSENT
 *      └──取消──> CANCELLED
 * </pre>
 */
public enum VisitStatus {

    PENDING("待走访"),
    DONE("已完成"),
    REFUSED("拒访"),
    ABSENT("无人"),
    CANCELLED("已取消");

    private final String label;

    VisitStatus(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return this != PENDING;
    }

    public static Set<VisitStatus> nextOf(VisitStatus from) {
        return from == PENDING
                ? Set.of(DONE, REFUSED, ABSENT, CANCELLED)
                : Set.of();
    }
}
'''

FILES['ops/constant/MatchResult.java'] = '''package com.yundao.bp.ops.constant;

/**
 * 人房匹配结果（对应 {@code bp_ops_house_visit.match_result}）。
 */
public enum MatchResult {

    MATCH("一致"),
    MISMATCH("不一致"),
    UNKNOWN("无法确认");

    private final String label;

    MatchResult(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }
}
'''

FILES['ops/entity/OpsHouseVisit.java'] = '''package com.yundao.bp.ops.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 巡房/入户走访。对应 {@code bp_ops_house_visit}。
 *
 * <p>用途：替代人工入户走访，落实"使用情况核查"——
 * 核验实际居住人是否与合同一致、是否转租转借、是否长期闲置。
 */
@Data
@TableName("bp_ops_house_visit")
public class OpsHouseVisit {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String visitNo;

    /** ROUTINE 例行 / VERIFY 使用核查 / COMPLAINT 投诉核查 / ALERT 预警核查 / VACANCY 空置核查 */
    private String visitType;

    private Long orgId;
    private Long spaceId;
    private Long houseId;
    private Long personId;

    private LocalDate planDate;
    private LocalDate actualDate;

    private Long visitUserId;
    private String visitUserName;
    private String triggerReason;
    private Long alertId;

    private Integer isOccupied;
    private Integer actualResidents;
    /** MATCH / MISMATCH / UNKNOWN */
    private String matchResult;

    private String findings;
    private Integer isSublease;
    private Integer isIdle;
    private Integer isIllegalUse;
    private String images;
    private String location;

    /** PENDING / DONE / REFUSED / ABSENT / CANCELLED */
    private String visitStatus;
    private String nextAction;
    private Long workorderId;

    private String createBy;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
'''

FILES['ops/mapper/OpsHouseVisitMapper.java'] = '''package com.yundao.bp.ops.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.ops.entity.OpsHouseVisit;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface OpsHouseVisitMapper extends BaseMapper<OpsHouseVisit> {
}
'''

FILES['ops/dto/VisitCreateCmd.java'] = '''package com.yundao.bp.ops.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import java.time.LocalDate;

/**
 * 创建走访任务。
 */
public record VisitCreateCmd(

        @NotBlank(message = "走访类型不能为空")
        @Pattern(regexp = "ROUTINE|VERIFY|COMPLAINT|ALERT|VACANCY", message = "走访类型不合法")
        String visitType,

        Long orgId,
        @NotNull(message = "走访房源不能为空")
        Long houseId,
        Long spaceId,
        Long personId,

        LocalDate planDate,

        Long visitUserId,
        String visitUserName,

        @Size(max = 500, message = "触发原因不能超过 500 字符")
        String triggerReason,

        Long alertId
) {
}
'''

FILES['ops/dto/VisitResultCmd.java'] = '''package com.yundao.bp.ops.dto;

import jakarta.validation.constraints.Pattern;
import java.time.LocalDate;

/**
 * 回填走访结果。
 *
 * @param visitStatus     DONE / REFUSED / ABSENT / CANCELLED
 * @param actualDate      实际走访日期
 * @param isOccupied      是否实际有人居住
 * @param actualResidents 实际居住人数
 * @param matchResult     MATCH / MISMATCH / UNKNOWN
 * @param findings        发现情况
 * @param isSublease      是否发现转租转借
 * @param isIdle          是否发现闲置
 * @param isIllegalUse    是否发现违规使用
 * @param images          现场照片
 * @param location        签到定位
 * @param nextAction      后续处置建议
 */
public record VisitResultCmd(

        @Pattern(regexp = "DONE|REFUSED|ABSENT|CANCELLED", message = "走访状态不合法")
        String visitStatus,

        LocalDate actualDate,
        Integer isOccupied,
        Integer actualResidents,

        @Pattern(regexp = "^$|MATCH|MISMATCH|UNKNOWN", message = "匹配结果不合法")
        String matchResult,

        String findings,
        Integer isSublease,
        Integer isIdle,
        Integer isIllegalUse,
        String images,
        String location,
        String nextAction
) {
}
'''

FILES['ops/dto/VisitVO.java'] = '''package com.yundao.bp.ops.dto;

import com.yundao.bp.ops.constant.MatchResult;
import com.yundao.bp.ops.constant.VisitStatus;
import com.yundao.bp.ops.entity.OpsHouseVisit;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 走访视图。
 */
public record VisitVO(
        Long id,
        String visitNo,
        String visitType,
        Long orgId,
        Long houseId,
        Long spaceId,
        Long personId,
        LocalDate planDate,
        LocalDate actualDate,
        Long visitUserId,
        String visitUserName,
        String triggerReason,
        Long alertId,
        Boolean occupied,
        Integer actualResidents,
        String matchResult,
        String matchResultLabel,
        String findings,
        Boolean sublease,
        Boolean idle,
        Boolean illegalUse,
        String images,
        String location,
        String visitStatus,
        String visitStatusLabel,
        String nextAction,
        Long workorderId,
        /** 派生：是否逾期未走访（计划日期已过但仍 PENDING） */
        Boolean overdue,
        LocalDateTime createTime
) {
    public static VisitVO from(OpsHouseVisit e) {
        if (e == null) {
            return null;
        }
        VisitStatus st;
        try {
            st = VisitStatus.valueOf(e.getVisitStatus());
        } catch (IllegalArgumentException ex) {
            st = VisitStatus.PENDING;
        }
        String mr = e.getMatchResult();
        String mrLabel = mr == null ? null : switch (mr) {
            case "MATCH" -> "一致";
            case "MISMATCH" -> "不一致";
            case "UNKNOWN" -> "无法确认";
            default -> mr;
        };
        boolean overdue = st == VisitStatus.PENDING && e.getPlanDate() != null
                && LocalDate.now().isAfter(e.getPlanDate());
        return new VisitVO(e.getId(), e.getVisitNo(), e.getVisitType(), e.getOrgId(),
                e.getHouseId(), e.getSpaceId(), e.getPersonId(), e.getPlanDate(),
                e.getActualDate(), e.getVisitUserId(), e.getVisitUserName(),
                e.getTriggerReason(), e.getAlertId(),
                e.getIsOccupied() != null && e.getIsOccupied() == 1,
                e.getActualResidents(), mr, mrLabel, e.getFindings(),
                e.getIsSublease() != null && e.getIsSublease() == 1,
                e.getIsIdle() != null && e.getIsIdle() == 1,
                e.getIsIllegalUse() != null && e.getIsIllegalUse() == 1,
                e.getImages(), e.getLocation(), e.getVisitStatus(), st.label(),
                e.getNextAction(), e.getWorkorderId(), overdue, e.getCreateTime());
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
