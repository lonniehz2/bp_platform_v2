package com.yundao.bp.biz.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 换房单。对应 {@code bp_biz_exchange}。
 *
 * <p><b>政策要点</b>：
 * <ul>
 *   <li><b>成都</b>：同一租期内限换 1 次（{@code exchange_times}）</li>
 *   <li><b>重庆</b>：期满因合住人数减少不符户型标准「应当换房」，
 *       应换不换按 <b>1.5 倍</b>计租（{@code no_exchange_flag} + {@code rent_multiplier}）</li>
 * </ul>
 */
@Data
@TableName("bp_biz_exchange")
public class BizExchange {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String exchangeNo;

    private Long personId;
    private Long oldContractId;
    private Long oldHouseId;
    private Long newHouseId;
    private Long newContractId;

    /** VOLUNTARY / ADJUST / EXPEL_RELOCATE */
    private String exchangeType;
    private String exchangeReason;

    /** APPLYING / APPROVING / APPROVED / COMPLETED / REJECTED */
    private String exchangeStatus;

    /** 权限是否已自动迁移 */
    private Integer grantMigrated;
    /** 本租期内第几次换房（成都限 1 次） */
    private Integer exchangeTimes;
    /** 是否应换房 */
    private Integer isForced;
    /** 应换不换标记（重庆按 1.5 倍计租） */
    private Integer noExchangeFlag;
    /** 换房后租金倍率 */
    private BigDecimal rentMultiplier;

    private Integer familySizeBefore;
    private Integer familySizeAfter;

    /** MARRIAGE / BIRTH / COHABIT / EMPLOYMENT / SCHOOL / OTHER */
    private String exchangeReasonCode;

    @TableField(fill = FieldFill.INSERT)
    private String createBy;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
