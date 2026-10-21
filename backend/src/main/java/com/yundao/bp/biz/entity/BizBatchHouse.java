package com.yundao.bp.biz.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 批次可配房源池。对应 {@code bp_biz_batch_house}。
 */
@Data
@TableName("bp_biz_batch_house")
public class BizBatchHouse {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private Long batchId;
    private Long houseId;
    private Long spaceId;
    /** AVAILABLE / LOCKED / SELECTED / REMOVED */
    private String inPoolStatus;

    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
