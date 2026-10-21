package com.yundao.bp.biz.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 摇号/选房结果。对应 {@code bp_biz_lottery_result}。
 */
@Data
@TableName("bp_biz_lottery_result")
public class BizLotteryResult {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private Long batchId;
    private Long personId;
    private Long applicationId;
    private Long waitingId;

    /** WON / LOST / WAITLIST / GIVE_UP */
    private String resultType;
    /** 摇号序号（随机生成，公证留痕） */
    private String lotterySeq;
    private Integer selectSeq;

    private Long houseId;
    private Long spaceId;
    private LocalDateTime selectTime;
    private String giveUpReason;

    /** PENDING / CONFIRMED / EXPIRED / GIVE_UP */
    private String resultStatus;

    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
