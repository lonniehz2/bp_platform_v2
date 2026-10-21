package com.yundao.bp.ops.entity;

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
