package com.yundao.bp.biz.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 配租单。对应 {@code bp_biz_allocation}。
 */
@Data
@TableName("bp_biz_allocation")
public class BizAllocation {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String allocationNo;
    private Long batchId;
    private Long personId;
    private Long houseId;
    private Long spaceId;

    /** LOTTERY / SELECT / DIRECT / EXCHANGE */
    private String allocationType;
    private LocalDate allocationDate;
    private LocalDate planRentStart;
    private LocalDate planRentEnd;

    /** PENDING_SIGN / SIGNED / CANCELLED / EXPIRED */
    private String allocationStatus;
    /** 房源锁定到期时间（超时自动释放） */
    private LocalDateTime lockExpireTime;
    private String giveUpReason;

    @TableField(fill = FieldFill.INSERT)
    private String createBy;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private String updateBy;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
