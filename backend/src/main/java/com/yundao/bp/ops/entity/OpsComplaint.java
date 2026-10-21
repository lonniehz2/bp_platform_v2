package com.yundao.bp.ops.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 投诉建议。对应 {@code bp_ops_complaint}。
 */
@Data
@TableName("bp_ops_complaint")
public class OpsComplaint {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String complaintNo;

    /** COMPLAINT 投诉 / SUGGEST 建议 / CONSULT 咨询 / PRAISE 表扬 */
    private String complaintType;
    /** MINIAPP / APP / PHONE / WALKIN / OTHER */
    private String source;

    private Long orgId;
    private Long personId;
    private String submitterName;
    private String submitterPhone;

    private String title;
    private String content;
    private String images;

    private Long workorderId;

    /** PENDING / HANDLING / HANDLED / CLOSED */
    private String handleStatus;
    private Long handleUserId;
    private LocalDateTime handleTime;
    private String handleResult;
    /** 满意度 1-5 */
    private Integer satisfaction;

    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
