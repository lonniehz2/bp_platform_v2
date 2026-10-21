package com.yundao.bp.dev.entity;

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
