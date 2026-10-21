package com.yundao.bp.grant.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 本地人员与 IoT 人员的映射。对应 `bp_grant_iot_person_map`。
 */
@Data
@TableName("bp_grant_iot_person_map")
public class GrantIotPersonMap {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private Long personId;
    /** IoT 人员主键 ownerId */
    private String iotOwnerId;
    private String iotOrganId;
    /** IoT 侧人员账号（手机号） */
    private String iotAccount;
    /** SYNCED / PENDING / FAILED */
    private String syncStatus;
    private LocalDateTime syncTime;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
