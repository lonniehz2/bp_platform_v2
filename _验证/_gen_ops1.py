# -*- coding: utf-8 -*-
"""生成 ops 告警工单模块（第 1 部分：常量/实体/Mapper/DTO）"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['ops/constant/WorkOrderStatus.java'] = '''package com.yundao.bp.ops.constant;

import java.util.Map;
import java.util.Set;

/**
 * 工单状态机（对应 {@code bp_ops_workorder.order_status}）。
 *
 * <pre>
 *   PENDING ──派单──> ASSIGNED ──接单──> ACCEPTED ──开始──> PROCESSING ──完工──> FINISHED ──闭环──> CLOSED
 *      │                 │                 │                    │
 *      └─────────────────┴─────────────────┴────────────────────┴──> CANCELLED（取消，终态）
 *                        └──驳回──> REJECTED（终态）
 * </pre>
 *
 * <p>业务约束：
 * <ul>
 *   <li>{@code CLOSED} 是唯一"闭环"终态，闭环时间是考核指标</li>
 *   <li>{@code FINISHED} 之后才能 {@code CLOSED}（先完工再确认）</li>
 *   <li>{@code REJECTED} / {@code CANCELLED} 为异常终态，不计入 SLA 达标</li>
 * </ul>
 */
public enum WorkOrderStatus {

    PENDING("待派单", false),
    ASSIGNED("已派单", false),
    ACCEPTED("已接单", false),
    PROCESSING("处理中", false),
    FINISHED("已完工", false),
    CLOSED("已闭环", true),
    CANCELLED("已取消", true),
    REJECTED("已驳回", true);

    private final String label;
    private final boolean terminal;

    WorkOrderStatus(String label, boolean terminal) {
        this.label = label;
        this.terminal = terminal;
    }

    public String label() {
        return label;
    }

    /** 是否终态（不可再流转）。 */
    public boolean isTerminal() {
        return terminal;
    }

    /** 是否仍在处理中（未终态）。 */
    public boolean isOpen() {
        return !terminal;
    }

    /** 允许的迁移。 */
    public static Set<WorkOrderStatus> nextOf(WorkOrderStatus from) {
        return switch (from) {
            case PENDING -> Set.of(ASSIGNED, CANCELLED);
            case ASSIGNED -> Set.of(ACCEPTED, REJECTED, CANCELLED);
            case ACCEPTED -> Set.of(PROCESSING, FINISHED, CANCELLED);
            case PROCESSING -> Set.of(FINISHED, CANCELLED);
            case FINISHED -> Set.of(CLOSED);
            case CLOSED, CANCELLED, REJECTED -> Set.of();
        };
    }

    /** 已派单/已接单/处理中 —— 用于"我的待办"统计。 */
    public static Set<WorkOrderStatus> IN_PROGRESS = Set.of(ASSIGNED, ACCEPTED, PROCESSING);

    public static Map<String, String> labels() {
        return java.util.Arrays.stream(values())
                .collect(java.util.stream.Collectors.toMap(Enum::name, WorkOrderStatus::label));
    }
}
'''

FILES['ops/constant/WorkOrderAction.java'] = '''package com.yundao.bp.ops.constant;

/**
 * 工单流转动作（对应 {@code bp_ops_workorder_log.action}）。
 */
public enum WorkOrderAction {

    CREATE("创建"),
    ASSIGN("派单"),
    ACCEPT("接单"),
    START("开始处理"),
    FINISH("完工"),
    CLOSE("闭环"),
    CANCEL("取消"),
    REJECT("驳回"),
    EVALUATE("评价"),
    REMARK("备注");

    private final String label;

    WorkOrderAction(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }
}
'''

FILES['ops/constant/SlaStatus.java'] = '''package com.yundao.bp.ops.constant;

/**
 * SLA 达标状态（对应 {@code bp_ops_workorder.sla_status}）。
 */
public enum SlaStatus {

    ON_TIME("按时"),
    RESPONSE_TIMEOUT("响应超时"),
    FINISH_TIMEOUT("完工超时");

    private final String label;

    SlaStatus(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }
}
'''

FILES['ops/entity/OpsWorkorder.java'] = '''package com.yundao.bp.ops.entity;

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
 * 工单。对应 {@code bp_ops_workorder}。
 */
@Data
@TableName("bp_ops_workorder")
public class OpsWorkorder {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String workorderNo;

    /** REPAIR / INSPECT / INSTALL / MAINTAIN / COMPLAINT / CONSULT / ALERT / VISIT */
    private String orderType;
    /** TENANT_APP / MINIAPP / STAFF / ALERT / PHONE / WALKIN / IMPORT */
    private String orderSource;

    private Long orgId;
    private Long spaceId;
    private Long houseId;
    private String deviceId;
    private String deviceType;

    private Long personId;
    private String reporterName;
    private String reporterPhone;

    private String orderTitle;
    private String orderContent;
    private String orderAddress;
    private String images;
    private String videos;

    private Long assignUserId;
    private String assignUserName;
    private String assignUserPhone;

    private LocalDateTime assignTime;
    private LocalDateTime acceptTime;
    private LocalDateTime arriveTime;
    private LocalDateTime finishTime;
    /** 闭环时间（考核用：闭环时间 - 报修时间） */
    private LocalDateTime closeTime;

    private Integer slaResponseMinutes;
    private Integer slaFinishMinutes;
    /** ON_TIME / RESPONSE_TIMEOUT / FINISH_TIMEOUT */
    private String slaStatus;

    private Integer isDeviceChanged;
    private String newDeviceMac;
    private Long changeLogId;

    /** PENDING / ASSIGNED / ACCEPTED / PROCESSING / FINISHED / CLOSED / CANCELLED / REJECTED */
    private String orderStatus;
    private String handleResult;

    private Integer isWarranty;
    private Integer evaluateScore;
    private String evaluateContent;
    private LocalDateTime evaluateTime;
    private BigDecimal costAmount;
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

FILES['ops/entity/OpsWorkorderLog.java'] = '''package com.yundao.bp.ops.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 工单流转记录（全留痕）。对应 {@code bp_ops_workorder_log}。
 */
@Data
@TableName("bp_ops_workorder_log")
public class OpsWorkorderLog {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private Long workorderId;

    /** CREATE / ASSIGN / ACCEPT / START / FINISH / CLOSE / CANCEL / REJECT / EVALUATE / REMARK */
    private String action;
    private String fromStatus;
    private String toStatus;
    private Long operatorId;
    private String operatorName;
    private String content;
    private String images;
    private LocalDateTime createTime;
}
'''

for mapper, entity in (('OpsWorkorderMapper', 'OpsWorkorder'),
                       ('OpsWorkorderLogMapper', 'OpsWorkorderLog')):
    FILES['ops/mapper/%s.java' % mapper] = '''package com.yundao.bp.ops.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.ops.entity.%s;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface %s extends BaseMapper<%s> {
}
''' % (entity, mapper, entity)

FILES['ops/dto/WorkOrderCreateCmd.java'] = '''package com.yundao.bp.ops.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/**
 * 创建工单。
 */
public record WorkOrderCreateCmd(

        @NotBlank(message = "工单类型不能为空")
        @Pattern(regexp = "REPAIR|INSPECT|INSTALL|MAINTAIN|COMPLAINT|CONSULT|ALERT|VISIT",
                message = "工单类型不合法")
        String orderType,

        @Pattern(regexp = "^$|TENANT_APP|MINIAPP|STAFF|ALERT|PHONE|WALKIN|IMPORT",
                message = "来源不合法")
        String orderSource,

        @NotBlank(message = "工单标题不能为空")
        @Size(max = 255, message = "标题不能超过 255 字符")
        String orderTitle,

        @Size(max = 2000, message = "问题描述不能超过 2000 字符")
        String orderContent,

        Long orgId,
        Long spaceId,
        Long houseId,
        String deviceId,
        String deviceType,
        Long personId,
        String reporterName,
        String reporterPhone,
        String orderAddress,
        String images,

        /** 响应时限（分钟），为空按工单类型默认值 */
        Integer slaResponseMinutes,
        /** 完工时限（分钟），为空按工单类型默认值 */
        Integer slaFinishMinutes,
        String remark
) {
}
'''

FILES['ops/dto/WorkOrderVO.java'] = '''package com.yundao.bp.ops.dto;

import com.yundao.bp.ops.constant.WorkOrderStatus;
import com.yundao.bp.ops.entity.OpsWorkorder;
import java.time.LocalDateTime;

/**
 * 工单视图（含派生指标）。
 */
public record WorkOrderVO(
        Long id,
        String workorderNo,
        String orderType,
        String orderSource,
        String orderTitle,
        String orderContent,
        String orderAddress,
        Long orgId,
        Long spaceId,
        Long houseId,
        String deviceId,
        Long personId,
        String reporterName,
        String reporterPhone,
        Long assignUserId,
        String assignUserName,
        String orderStatus,
        String orderStatusLabel,
        String slaStatus,
        /** 派生：是否已超响应时限（未接单且已超时） */
        Boolean responseOverdue,
        /** 派生：是否已超完工时限（未完工且已超时） */
        Boolean finishOverdue,
        LocalDateTime assignTime,
        LocalDateTime acceptTime,
        LocalDateTime finishTime,
        LocalDateTime closeTime,
        String handleResult,
        Integer evaluateScore,
        LocalDateTime createTime
) {
    public static WorkOrderVO from(OpsWorkorder e) {
        if (e == null) {
            return null;
        }
        WorkOrderStatus st;
        try {
            st = WorkOrderStatus.valueOf(e.getOrderStatus());
        } catch (IllegalArgumentException ex) {
            st = WorkOrderStatus.PENDING;
        }
        LocalDateTime now = LocalDateTime.now();
        boolean responseOverdue = false;
        if (e.getAcceptTime() == null && e.getSlaResponseMinutes() != null
                && e.getCreateTime() != null && st.isOpen()) {
            responseOverdue = now.isAfter(
                    e.getCreateTime().plusMinutes(e.getSlaResponseMinutes()));
        }
        boolean finishOverdue = false;
        if (e.getFinishTime() == null && e.getSlaFinishMinutes() != null
                && e.getCreateTime() != null && st.isOpen()) {
            finishOverdue = now.isAfter(
                    e.getCreateTime().plusMinutes(e.getSlaFinishMinutes()));
        }
        return new WorkOrderVO(e.getId(), e.getWorkorderNo(), e.getOrderType(),
                e.getOrderSource(), e.getOrderTitle(), e.getOrderContent(), e.getOrderAddress(),
                e.getOrgId(), e.getSpaceId(), e.getHouseId(), e.getDeviceId(), e.getPersonId(),
                e.getReporterName(), e.getReporterPhone(), e.getAssignUserId(),
                e.getAssignUserName(), e.getOrderStatus(), st.label(), e.getSlaStatus(),
                responseOverdue, finishOverdue, e.getAssignTime(), e.getAcceptTime(),
                e.getFinishTime(), e.getCloseTime(), e.getHandleResult(), e.getEvaluateScore(),
                e.getCreateTime());
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
