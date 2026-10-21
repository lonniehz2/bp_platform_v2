# -*- coding: utf-8 -*-
"""生成 ops 告警中心（第 1 部分）"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['ops/constant/AlertStatus.java'] = '''package com.yundao.bp.ops.constant;

import java.util.Map;
import java.util.Set;

/**
 * 告警状态机（对应 {@code bp_ops_alert.alert_status}）。
 *
 * <pre>
 *   PENDING ──处置──> HANDLING ──办结──> HANDLED（闭环）
 *      │                 │
 *      ├──误报───────────┴──> IGNORED（终态）
 *      └──超时/重大──> ESCALATED（已升级，仍可继续处置）
 * </pre>
 */
public enum AlertStatus {

    PENDING("待处理", false),
    HANDLING("处理中", false),
    HANDLED("已闭环", true),
    IGNORED("误报忽略", true),
    ESCALATED("已升级", false);

    private final String label;
    private final boolean terminal;

    AlertStatus(String label, boolean terminal) {
        this.label = label;
        this.terminal = terminal;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return terminal;
    }

    /** 是否仍未闭环（用于"待处理告警数"统计）。 */
    public boolean isOpen() {
        return !terminal;
    }

    public static Set<AlertStatus> nextOf(AlertStatus from) {
        return switch (from) {
            case PENDING -> Set.of(HANDLING, IGNORED, ESCALATED);
            case ESCALATED -> Set.of(HANDLING, IGNORED);
            case HANDLING -> Set.of(HANDLED, IGNORED, ESCALATED);
            case HANDLED, IGNORED -> Set.of();
        };
    }

    public static Map<String, String> labels() {
        return java.util.Arrays.stream(values())
                .collect(java.util.stream.Collectors.toMap(Enum::name, AlertStatus::label));
    }
}
'''

FILES['ops/constant/AlertLevel.java'] = '''package com.yundao.bp.ops.constant;

/**
 * 告警级别（对应 {@code bp_ops_alert.alert_level}）。
 *
 * <p>级别决定 SLA 与是否推送短信/大屏红色告警：
 * {@code URGENT} 立即处置，{@code IMPORTANT} 当日处置，{@code NORMAL} 按常规流转。
 */
public enum AlertLevel {

    URGENT("紧急", 1),
    IMPORTANT("重要", 2),
    NORMAL("一般", 3);

    private final String label;
    private final int weight;

    AlertLevel(String label, int weight) {
        this.label = label;
        this.weight = weight;
    }

    public String label() {
        return label;
    }

    /** 权重（1 最高），用于排序。 */
    public int weight() {
        return weight;
    }
}
'''

FILES['ops/constant/AlertCategory.java'] = '''package com.yundao.bp.ops.constant;

/**
 * 告警类别（对应 {@code bp_ops_alert.alert_category}）。
 */
public enum AlertCategory {

    SAFETY("安全类"),
    DEVICE("设备类"),
    BUSINESS("业务类"),
    VIOLATION("违规类");

    private final String label;

    AlertCategory(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }
}
'''

FILES['ops/entity/OpsAlert.java'] = '''package com.yundao.bp.ops.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 告警事件（统一告警中心）。对应 {@code bp_ops_alert}。
 */
@Data
@TableName("bp_ops_alert")
public class OpsAlert {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String alertNo;

    private Long ruleId;
    private String ruleCode;

    /** SAFETY / DEVICE / BUSINESS / VIOLATION */
    private String alertCategory;
    /** SUBLEASE / IDLE / CONTRACT_EXPIRE / DEVICE_OFFLINE / LOW_BATTERY / TAMPER / ... */
    private String alertType;
    /** URGENT / IMPORTANT / NORMAL */
    private String alertLevel;

    private String alertTitle;
    private String alertContent;
    /** 触发值（如占比 25%） */
    private String alertValue;
    /** 阈值快照 */
    private String thresholdValue;

    private Long orgId;
    private Long spaceId;
    private Long houseId;
    private Long personId;
    private String deviceId;
    private Long contractId;
    private String relatedIds;

    /** PENDING / HANDLING / HANDLED / IGNORED / ESCALATED */
    private String alertStatus;
    private Long handleUserId;
    private LocalDateTime handleTime;
    private String handleAction;
    private String handleResult;
    private Long workorderId;
    private LocalDateTime escalateTime;

    private LocalDateTime alertTime;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
'''

FILES['ops/mapper/OpsAlertMapper.java'] = '''package com.yundao.bp.ops.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.ops.entity.OpsAlert;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface OpsAlertMapper extends BaseMapper<OpsAlert> {
}
'''

FILES['ops/dto/AlertCreateCmd.java'] = '''package com.yundao.bp.ops.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/**
 * 创建告警（可由规则引擎、设备回调或人工上报触发）。
 */
public record AlertCreateCmd(

        @NotBlank(message = "告警类别不能为空")
        @Pattern(regexp = "SAFETY|DEVICE|BUSINESS|VIOLATION", message = "告警类别不合法")
        String alertCategory,

        @NotBlank(message = "告警类型不能为空")
        @Size(max = 40, message = "告警类型不能超过 40 字符")
        String alertType,

        @NotBlank(message = "告警级别不能为空")
        @Pattern(regexp = "URGENT|IMPORTANT|NORMAL", message = "告警级别不合法")
        String alertLevel,

        @NotBlank(message = "告警标题不能为空")
        @Size(max = 255, message = "标题不能超过 255 字符")
        String alertTitle,

        @Size(max = 2000, message = "告警内容不能超过 2000 字符")
        String alertContent,

        String alertValue,
        String thresholdValue,

        Long ruleId,
        String ruleCode,
        Long orgId,
        Long spaceId,
        Long houseId,
        Long personId,
        String deviceId,
        Long contractId,
        String relatedIds
) {
}
'''

FILES['ops/dto/AlertVO.java'] = '''package com.yundao.bp.ops.dto;

import com.yundao.bp.ops.constant.AlertStatus;
import com.yundao.bp.ops.entity.OpsAlert;
import java.time.LocalDateTime;

/**
 * 告警视图。
 */
public record AlertVO(
        Long id,
        String alertNo,
        String alertCategory,
        String alertType,
        String alertLevel,
        String alertLevelLabel,
        String alertTitle,
        String alertContent,
        String alertValue,
        String thresholdValue,
        Long orgId,
        Long spaceId,
        Long houseId,
        Long personId,
        String deviceId,
        String alertStatus,
        String alertStatusLabel,
        Long handleUserId,
        LocalDateTime handleTime,
        String handleResult,
        Long workorderId,
        LocalDateTime alertTime,
        LocalDateTime createTime
) {
    public static AlertVO from(OpsAlert e) {
        if (e == null) {
            return null;
        }
        AlertStatus st;
        try {
            st = AlertStatus.valueOf(e.getAlertStatus());
        } catch (IllegalArgumentException ex) {
            st = AlertStatus.PENDING;
        }
        String levelLabel = switch (e.getAlertLevel() == null ? "" : e.getAlertLevel()) {
            case "URGENT" -> "紧急";
            case "IMPORTANT" -> "重要";
            case "NORMAL" -> "一般";
            default -> e.getAlertLevel();
        };
        return new AlertVO(e.getId(), e.getAlertNo(), e.getAlertCategory(), e.getAlertType(),
                e.getAlertLevel(), levelLabel, e.getAlertTitle(), e.getAlertContent(),
                e.getAlertValue(), e.getThresholdValue(), e.getOrgId(), e.getSpaceId(),
                e.getHouseId(), e.getPersonId(), e.getDeviceId(), e.getAlertStatus(),
                st.label(), e.getHandleUserId(), e.getHandleTime(), e.getHandleResult(),
                e.getWorkorderId(), e.getAlertTime(), e.getCreateTime());
    }
}
'''

FILES['ops/dto/AlertStatsVO.java'] = '''package com.yundao.bp.ops.dto;

import java.util.Map;

/**
 * 告警统计（驾驶舱 / 大屏用）。
 *
 * @param total      总数
 * @param pending    待处理（PENDING + ESCALATED）
 * @param handling   处理中
 * @param handled    已闭环
 * @param ignored    误报忽略
 * @param byLevel    按级别分布
 * @param byCategory 按类别分布
 * @param urgentOpen 紧急且未闭环 —— 大屏红色告警数
 */
public record AlertStatsVO(
        long total,
        long pending,
        long handling,
        long handled,
        long ignored,
        Map<String, Long> byLevel,
        Map<String, Long> byCategory,
        long urgentOpen
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
