package com.yundao.bp.ops.entity;

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
