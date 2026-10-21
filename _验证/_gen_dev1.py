# -*- coding: utf-8 -*-
"""生成通行记录 + 授权审计（实体 + Mapper + 服务 + 接口）"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
F = {}

# ==================== 实体 ====================
F['dev/entity/DevAccessRecord.java'] = '''package com.yundao.bp.dev.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 开门记录。对应 `bp_dev_access_record`（按月分区大表）。
 *
 * <p>⭐ 这是「行为轨迹」「空置判定」「异常开门」的<b>唯一数据源</b>。
 * 写入必须按 {@code event_id} 幂等（回调可能重发）。
 */
@Data
@TableName("bp_dev_access_record")
public class DevAccessRecord {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    /** IoT 事件ID（幂等去重，唯一） */
    private String eventId;

    private String deviceId;
    private String lockId;
    private String deviceMac;

    private Long spaceId;
    private Long houseId;
    private Long orgId;

    /** 开门方式码（IoT 字典 1001-1049） */
    private String openType;
    private String openTypeName;
    /** 是否可信开门方式（用于不可信占比预警） */
    private Integer isTrusted;

    private Long personId;
    private String targetUserMobile;

    private LocalDateTime openTime;
    /** CALLBACK 回调 / PULL 拉取补齐 */
    private String source;
    private Integer isAbnormal;
    /** DURESS / RETRY / OFFHOURS / OTHER */
    private String abnormalType;

    private LocalDateTime createTime;
}
'''

F['grant/entity/GrantAuditLog.java'] = '''package com.yundao.bp.grant.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 授权操作审计。对应 `bp_grant_audit_log`。
 *
 * <p>⭐ ★ 级要求：授权操作必须<b>不可篡改可追溯</b>。
 * 因此本模块<b>不提供 update / delete 接口</b>，只追加。
 */
@Data
@TableName("bp_grant_audit_log")
public class GrantAuditLog {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    /** GRANT / REVOKE / FREEZE / UNFREEZE / TRANSFER */
    private String bizType;
    private Long bizId;

    private Long personId;
    private Long spaceId;

    private Long operatorId;
    private String operatorName;
    private String reason;

    private String beforeJson;
    private String afterJson;
    /** SUCCESS / FAILED */
    private String result;

    private LocalDateTime createTime;
}
'''

F['dev/mapper/DevAccessRecordMapper.java'] = '''package com.yundao.bp.dev.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.dev.entity.DevAccessRecord;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface DevAccessRecordMapper extends BaseMapper<DevAccessRecord> {
}
'''

F['grant/mapper/GrantAuditLogMapper.java'] = '''package com.yundao.bp.grant.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.grant.entity.GrantAuditLog;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface GrantAuditLogMapper extends BaseMapper<GrantAuditLog> {
}
'''

# ==================== 通行记录服务 ====================
F['dev/service/AccessRecordService.java'] = '''package com.yundao.bp.dev.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.dev.dto.AccessReportCmd;
import com.yundao.bp.dev.dto.AccessVO;
import com.yundao.bp.dev.dto.IdleStatVO;
import com.yundao.bp.dev.dto.TraceVO;
import java.time.LocalDate;
import java.util.List;

/**
 * 通行记录服务。
 *
 * <p>⭐ 支撑三项 ★ 级能力：
 * <ol>
 *   <li><b>行为轨迹</b>：按人/房源查开门时间线</li>
 *   <li><b>空置判定</b>：房源连续 N 天无开门记录 → 疑似空置</li>
 *   <li><b>异常开门</b>：挟持/试错/非授权时段，触发告警</li>
 * </ol>
 */
public interface AccessRecordService {

    /**
     * 上报开门记录（IoT 回调或拉取补齐）。
     *
     * <p><b>幂等</b>：按 {@code event_id} 去重，重复上报返回 false。
     *
     * @return true=新写入，false=重复
     */
    boolean report(AccessReportCmd cmd);

    /** 批量上报。 */
    int reportBatch(List<AccessReportCmd> cmds);

    PageResult<AccessVO> page(long pageNum, long pageSize, Long personId, Long houseId,
                              LocalDate dateFrom, LocalDate dateTo, Boolean abnormalOnly);

    /** ⭐ 行为轨迹：某人在区间的开门时间线。 */
    TraceVO traceByPerson(Long personId, LocalDate dateFrom, LocalDate dateTo);

    /** ⭐ 行为轨迹：某房源在区间的开门时间线。 */
    TraceVO traceByHouse(Long houseId, LocalDate dateFrom, LocalDate dateTo);

    /** ⭐ 空置判定：连续无开门天数 ≥ 阈值视为疑似空置。 */
    List<IdleStatVO> detectIdle(Long orgId, int idleDays);

    /** 不可信开门占比统计（考核用）。 */
    java.util.Map<String, Object> untrustedRatio(Long orgId, LocalDate dateFrom,
                                                 LocalDate dateTo);
}
'''

F['dev/dto/AccessReportCmd.java'] = '''package com.yundao.bp.dev.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;

/**
 * 上报一条开门记录。
 *
 * <p>{@code eventId} 是幂等键，必须由 IoT 侧提供且唯一。
 */
public record AccessReportCmd(

        @NotBlank(message = "事件ID不能为空（幂等去重）")
        String eventId,

        String lockId,
        String deviceId,
        String deviceMac,

        Long spaceId,
        Long houseId,
        Long orgId,

        @NotBlank(message = "开门方式不能为空")
        String openType,

        Long personId,
        String targetUserMobile,

        @NotNull(message = "开门时间不能为空")
        LocalDateTime openTime,

        /** CALLBACK / PULL */
        String source,

        Boolean abnormal,
        String abnormalType
) {
}
'''

F['dev/dto/AccessVO.java'] = '''package com.yundao.bp.dev.dto;

import com.yundao.bp.dev.entity.DevAccessRecord;
import java.time.LocalDateTime;

/**
 * 开门记录视图。
 */
public record AccessVO(
        Long id,
        String eventId,
        String lockId,
        Long houseId,
        Long spaceId,
        Long personId,
        String targetUserMobile,
        String openType,
        String openTypeName,
        Boolean trusted,
        LocalDateTime openTime,
        String source,
        Boolean abnormal,
        String abnormalType
) {
    public static AccessVO from(DevAccessRecord e) {
        if (e == null) {
            return null;
        }
        return new AccessVO(e.getId(), e.getEventId(), e.getLockId(), e.getHouseId(),
                e.getSpaceId(), e.getPersonId(), e.getTargetUserMobile(), e.getOpenType(),
                e.getOpenTypeName(), e.getIsTrusted() != null && e.getIsTrusted() == 1,
                e.getOpenTime(), e.getSource(),
                e.getIsAbnormal() != null && e.getIsAbnormal() == 1, e.getAbnormalType());
    }
}
'''

F['dev/dto/TraceVO.java'] = '''package com.yundao.bp.dev.dto;

import java.time.LocalDate;
import java.util.List;

/**
 * 行为轨迹。
 */
public record TraceVO(
        String scope,
        Long targetId,
        LocalDate dateFrom,
        LocalDate dateTo,
        int totalRecords,
        int abnormalRecords,
        String summary,
        List<AccessVO> timeline
) {
}
'''

F['dev/dto/IdleStatVO.java'] = '''package com.yundao.bp.dev.dto;

import java.time.LocalDateTime;

/**
 * 空置判定结果。
 */
public record IdleStatVO(
        Long houseId,
        Long spaceId,
        Long orgId,
        /** 最近一次开门时间（无记录则为 null） */
        LocalDateTime lastOpenTime,
        /** 连续无开门天数 */
        long idleDays,
        /** 是否疑似空置 */
        boolean suspectIdle,
        String remark
) {
}
'''

count = 0
for rel, content in F.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个文件' % count)
