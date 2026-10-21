package com.yundao.bp.biz.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 配租批次。对应 {@code bp_biz_batch}。
 */
@Data
@TableName("bp_biz_batch")
public class BizBatch {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String batchNo;
    private String batchName;
    private Long orgId;
    private String securityType;

    /** LOTTERY / SELECT / DIRECT / SUPPLEMENT */
    private String batchType;

    private Integer houseCount;
    private Integer applicantCount;

    private LocalDateTime signupStart;
    private LocalDateTime signupEnd;
    private LocalDateTime lotteryTime;
    private LocalDateTime selectStart;
    private LocalDateTime selectEnd;

    /** 摇号随机种子（公证留痕，可复现） */
    private String lotterySeed;
    private String lotteryAlgo;
    private String notaryInfo;

    /** DRAFT / PUBLISHED / SIGNUP / LOTTERY / LOTTERY_DONE / SELECTING / ALLOCATED / CLOSED / CANCELLED */
    private String batchStatus;
    private String ruleConfig;
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
