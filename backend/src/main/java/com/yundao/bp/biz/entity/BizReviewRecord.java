package com.yundao.bp.biz.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 审核记录（多级/多部门联审）。对应 {@code bp_biz_review_record}。
 */
@Data
@TableName("bp_biz_review_record")
public class BizReviewRecord {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private Long applicationId;

    private Integer reviewRound;
    /** ACCEPT / FORM / JOINT / FINAL */
    private String reviewStage;
    /** REAL_ESTATE / CIVIL / SOCIAL_SECURITY ... */
    private String reviewDept;
    /** API / BATCH / MANUAL */
    private String reviewType;

    private Long reviewUserId;
    private String reviewUserName;
    private LocalDateTime reviewTime;

    /** PASS / REJECT / SUPPLEMENT */
    private String reviewResult;
    /** 核验项明细（JSON） */
    private String checkItems;
    private BigDecimal score;
    private String reviewOpinion;

    private String adapterRequest;
    private String adapterResponse;

    private LocalDateTime createTime;
}
