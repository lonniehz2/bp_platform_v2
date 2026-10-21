package com.yundao.bp.ops.entity;

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
