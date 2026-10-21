# -*- coding: utf-8 -*-
"""生成 grant 授权编排模块（第 1 部分：常量/实体/Mapper/DTO）"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['grant/constant/GrantStatus.java'] = '''package com.yundao.bp.grant.constant;

import java.util.Map;
import java.util.Set;

/**
 * 权益状态机（对应 {@code bp_grant_entitlement.grant_status}）。
 *
 * <pre>
 *   PENDING ──生效时间到──> EFFECTIVE ──到期──> EXPIRED
 *      │                       │
 *      │                       ├──欠费/违规──> FROZEN ──解除──> EFFECTIVE
 *      │                       └──撤销/退租──> REVOKED（终态）
 *      └──撤销──> REVOKED（终态）
 * </pre>
 */
public enum GrantStatus {

    PENDING("待生效"),
    EFFECTIVE("已生效"),
    EXPIRED("已到期"),
    FROZEN("已冻结"),
    REVOKED("已撤销");

    private final String label;

    GrantStatus(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 允许的迁移。REVOKED / EXPIRED 为终态。 */
    public static Set<GrantStatus> nextOf(GrantStatus from) {
        return switch (from) {
            case PENDING -> Set.of(EFFECTIVE, REVOKED);
            case EFFECTIVE -> Set.of(EXPIRED, FROZEN, REVOKED);
            case FROZEN -> Set.of(EFFECTIVE, REVOKED);
            case EXPIRED, REVOKED -> Set.of();
        };
    }

    /** 是否终态（不可再变更）。 */
    public boolean isTerminal() {
        return this == REVOKED || this == EXPIRED;
    }

    /** 是否占用配额/算有效权益。 */
    public boolean isActive() {
        return this == EFFECTIVE;
    }

    public static Map<String, String> labels() {
        return java.util.Arrays.stream(values())
                .collect(java.util.stream.Collectors.toMap(Enum::name, GrantStatus::label));
    }
}
'''

FILES['grant/constant/GrantTaskStatus.java'] = '''package com.yundao.bp.grant.constant;

/**
 * 授权任务状态（对应 {@code bp_grant_task.task_status}）。
 *
 * <pre>
 *   PENDING ──消费者取到──> DISPATCHING ──成功──> SUCCESS
 *      │                        │
 *      │                        ├──部分失败──> PARTIAL
 *      │                        └──失败(可重试)──> PENDING（retryCount++）
 *      │                                              └─超限─> FAILED
 *      └──IoT 返回异步 taskId──> DISPATCHING（等轮询结果）
 * </pre>
 */
public enum GrantTaskStatus {

    PENDING("待下发"),
    DISPATCHING("下发中"),
    SUCCESS("成功"),
    PARTIAL("部分成功"),
    FAILED("失败");

    private final String label;

    GrantTaskStatus(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 是否已结束（不再重试/轮询）。 */
    public boolean isFinished() {
        return this == SUCCESS || this == PARTIAL || this == FAILED;
    }
}
'''

FILES['grant/entity/GrantEntitlement.java'] = '''package com.yundao.bp.grant.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 权益（授权）主表。对应 {@code bp_grant_entitlement}。
 *
 * <p>一条权益 = 某个持有者对某个空间/房源在某个时段内的权限集合。
 */
@Data
@TableName("bp_grant_entitlement")
public class GrantEntitlement {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String grantNo;

    /** OWNERSHIP / MANAGEMENT / USAGE / VISIT */
    private String grantLevel;
    /** PERSON / ORG */
    private String holderType;
    private Long personId;
    private Long orgId;

    /** 权限锚点空间（向下继承） */
    private Long spaceId;
    private String spacePath;
    private Long houseId;

    private LocalDateTime validStart;
    private LocalDateTime validEnd;

    private Integer allowOpen;
    private Integer allowManage;
    private Integer allowDelegate;

    private Integer visitLimitTimes;
    private Integer visitUsedTimes;

    /** CONTRACT / TRANSFER / DELEGATE / ... */
    private String sourceType;
    private Long sourceId;
    private Long parentGrantId;

    /** PENDING / EFFECTIVE / EXPIRED / FROZEN / REVOKED */
    private String grantStatus;
    private String freezeReason;
    private String revokeReason;
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

FILES['grant/entity/GrantTask.java'] = '''package com.yundao.bp.grant.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 授权下发任务。对应 {@code bp_grant_task}。
 *
 * <p>幂等键 {@code idempotent_key} 在库上有唯一索引，防止重复下发。
 */
@Data
@TableName("bp_grant_task")
public class GrantTask {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String taskNo;

    /** sha1(personId + spaceId + level + 有效期) —— 库上唯一 */
    private String idempotentKey;

    /** GRANT / REVOKE / FREEZE / UNFREEZE */
    private String taskType;

    private Long personId;
    private Long entitlementId;
    /** 逗号分隔的钥匙包 ID */
    private String keyringIds;

    private Integer lockCount;
    private Integer successCount;
    private Integer failCount;

    private LocalDateTime validStart;
    private LocalDateTime validEnd;

    /** IoT 异步任务 ID（用于 syncTask/result/list 轮询） */
    private String iotTaskId;
    private String iotRequestNo;

    /** PENDING / DISPATCHING / SUCCESS / PARTIAL / FAILED */
    private String taskStatus;
    private Integer retryCount;
    private String lastError;

    /** CONTRACT / KEYRING_ADD / SPACE_CHANGE / MANUAL */
    private String triggerSource;

    private String createBy;
    private LocalDateTime createTime;
    private LocalDateTime dispatchTime;
    private LocalDateTime finishTime;
    private LocalDateTime updateTime;
}
'''

FILES['grant/entity/GrantTaskDetail.java'] = '''package com.yundao.bp.grant.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 授权下发明细（每设备一行）。对应 {@code bp_grant_task_detail}。
 */
@Data
@TableName("bp_grant_task_detail")
public class GrantTaskDetail {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private Long taskId;
    private String deviceId;
    private String deviceMac;
    private String lockId;
    private Long spaceId;
    private Long keyringId;

    /** PENDING / SUCCESS / FAILED / SKIPPED */
    private String detailStatus;
    private String errorCode;
    private String errorMsg;
    private Integer durationMs;

    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
'''

for mapper in ('GrantEntitlementMapper', 'GrantTaskMapper', 'GrantTaskDetailMapper'):
    entity = {'GrantEntitlementMapper': 'GrantEntitlement',
              'GrantTaskMapper': 'GrantTask',
              'GrantTaskDetailMapper': 'GrantTaskDetail'}[mapper]
    FILES['grant/mapper/%s.java' % mapper] = '''package com.yundao.bp.grant.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.grant.entity.%s;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface %s extends BaseMapper<%s> {
}
''' % (entity, mapper, entity)

FILES['grant/dto/GrantApplyCmd.java'] = '''package com.yundao.bp.grant.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import java.time.LocalDateTime;
import java.util.List;

/**
 * 授权申请。
 *
 * @param personId   被授权人员
 * @param spaceId    权限锚点空间（房源/房间节点）
 * @param grantLevel OWNERSHIP / MANAGEMENT / USAGE / VISIT
 * @param validStart 生效时间（为空=立即）
 * @param validEnd   失效时间（为空=永久，仅 OWNERSHIP 允许）
 * @param keyringIds 使用的钥匙包 ID 列表（为空=仅下发 App 权限）
 * @param sourceType 来源：CONTRACT / MANUAL / DELEGATE
 * @param sourceId   来源单据 ID
 * @param remark     备注
 */
public record GrantApplyCmd(

        @NotNull(message = "人员不能为空")
        Long personId,

        @NotNull(message = "授权空间不能为空")
        Long spaceId,

        @NotBlank(message = "权限层级不能为空")
        @Pattern(regexp = "OWNERSHIP|MANAGEMENT|USAGE|VISIT", message = "权限层级不合法")
        String grantLevel,

        LocalDateTime validStart,
        LocalDateTime validEnd,

        List<Long> keyringIds,

        @Pattern(regexp = "^$|CONTRACT|MANUAL|DELEGATE|TRANSFER", message = "来源类型不合法")
        String sourceType,

        Long sourceId,
        String remark
) {
}
'''

FILES['grant/dto/GrantVO.java'] = '''package com.yundao.bp.grant.dto;

import com.yundao.bp.grant.constant.GrantStatus;
import com.yundao.bp.grant.entity.GrantEntitlement;
import java.time.LocalDateTime;

/**
 * 权益视图。
 */
public record GrantVO(
        Long id,
        String grantNo,
        Long personId,
        Long spaceId,
        Long houseId,
        String grantLevel,
        LocalDateTime validStart,
        LocalDateTime validEnd,
        Boolean allowOpen,
        Integer visitLimitTimes,
        Integer visitUsedTimes,
        String grantStatus,
        String grantStatusLabel,
        String sourceType,
        Long sourceId,
        String remark,
        LocalDateTime createTime
) {
    public static GrantVO from(GrantEntitlement e) {
        if (e == null) {
            return null;
        }
        GrantStatus st;
        try {
            st = GrantStatus.valueOf(e.getGrantStatus());
        } catch (IllegalArgumentException ex) {
            st = GrantStatus.PENDING;
        }
        return new GrantVO(e.getId(), e.getGrantNo(), e.getPersonId(), e.getSpaceId(),
                e.getHouseId(), e.getGrantLevel(), e.getValidStart(), e.getValidEnd(),
                e.getAllowOpen() != null && e.getAllowOpen() == 1,
                e.getVisitLimitTimes(), e.getVisitUsedTimes(),
                e.getGrantStatus(), st.label(), e.getSourceType(), e.getSourceId(),
                e.getRemark(), e.getCreateTime());
    }
}
'''

FILES['grant/dto/GrantTaskVO.java'] = '''package com.yundao.bp.grant.dto;

import com.yundao.bp.grant.constant.GrantTaskStatus;
import com.yundao.bp.grant.entity.GrantTask;
import java.time.LocalDateTime;

/**
 * 授权任务视图。
 */
public record GrantTaskVO(
        Long id,
        String taskNo,
        String taskType,
        Long personId,
        Long entitlementId,
        Integer lockCount,
        Integer successCount,
        Integer failCount,
        String iotTaskId,
        String taskStatus,
        String taskStatusLabel,
        Integer retryCount,
        String lastError,
        String triggerSource,
        LocalDateTime dispatchTime,
        LocalDateTime finishTime,
        LocalDateTime createTime
) {
    public static GrantTaskVO from(GrantTask t) {
        if (t == null) {
            return null;
        }
        GrantTaskStatus st;
        try {
            st = GrantTaskStatus.valueOf(t.getTaskStatus());
        } catch (IllegalArgumentException ex) {
            st = GrantTaskStatus.PENDING;
        }
        return new GrantTaskVO(t.getId(), t.getTaskNo(), t.getTaskType(), t.getPersonId(),
                t.getEntitlementId(), t.getLockCount(), t.getSuccessCount(), t.getFailCount(),
                t.getIotTaskId(), t.getTaskStatus(), st.label(), t.getRetryCount(),
                t.getLastError(), t.getTriggerSource(), t.getDispatchTime(), t.getFinishTime(),
                t.getCreateTime());
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
