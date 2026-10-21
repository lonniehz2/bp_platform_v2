# -*- coding: utf-8 -*-
"""生成换房模块（常量 + 实体 + DTO）"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['biz/constant/ExchangeType.java'] = '''package com.yundao.bp.biz.constant;

/**
 * 换房类型（对应 {@code bp_biz_exchange.exchange_type}）。
 */
public enum ExchangeType {

    VOLUNTARY("自愿换房"),
    ADJUST("调整换房"),
    EXPEL_RELOCATE("清退安置");

    private final String label;

    ExchangeType(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }
}
'''

FILES['biz/constant/ExchangeStatus.java'] = '''package com.yundao.bp.biz.constant;

import java.util.Set;

/**
 * 换房状态（对应 {@code bp_biz_exchange.exchange_status}）。
 *
 * <pre>
 *   APPLYING 申请中 → APPROVING 审批中 → APPROVED 已批准 → COMPLETED 已完成（终态）
 *                          └──驳回──> REJECTED（终态）
 * </pre>
 */
public enum ExchangeStatus {

    APPLYING("申请中", false),
    APPROVING("审批中", false),
    APPROVED("已批准", false),
    COMPLETED("已完成", true),
    REJECTED("已驳回", true);

    private final String label;
    private final boolean terminal;

    ExchangeStatus(String label, boolean terminal) {
        this.label = label;
        this.terminal = terminal;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return terminal;
    }

    public static Set<ExchangeStatus> nextOf(ExchangeStatus from) {
        return switch (from) {
            case APPLYING -> Set.of(APPROVING, REJECTED);
            case APPROVING -> Set.of(APPROVED, REJECTED);
            case APPROVED -> Set.of(COMPLETED, REJECTED);
            case COMPLETED, REJECTED -> Set.of();
        };
    }
}
'''

FILES['biz/entity/BizExchange.java'] = '''package com.yundao.bp.biz.entity;

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
'''

FILES['biz/mapper/BizExchangeMapper.java'] = '''package com.yundao.bp.biz.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.biz.entity.BizExchange;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface BizExchangeMapper extends BaseMapper<BizExchange> {
}
'''

FILES['biz/dto/ExchangeCreateCmd.java'] = '''package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;

/**
 * 申请换房。
 *
 * @param forceExchange 是否属于"应当换房"（如期满时合住人数减少不符户型标准）
 */
public record ExchangeCreateCmd(

        @NotNull(message = "人员不能为空")
        Long personId,

        @NotNull(message = "原合同不能为空")
        Long oldContractId,

        @NotNull(message = "原房源不能为空")
        Long oldHouseId,

        @NotNull(message = "新房源不能为空")
        Long newHouseId,

        @NotBlank(message = "换房类型不能为空")
        @Pattern(regexp = "VOLUNTARY|ADJUST|EXPEL_RELOCATE", message = "换房类型不合法")
        String exchangeType,

        String exchangeReason,

        /** 换房原因码：MARRIAGE / BIRTH / COHABIT / EMPLOYMENT / SCHOOL / OTHER */
        String exchangeReasonCode,

        Integer familySizeBefore,
        Integer familySizeAfter,

        Boolean forceExchange
) {
}
'''

FILES['biz/dto/ExchangeVO.java'] = '''package com.yundao.bp.biz.dto;

import com.yundao.bp.biz.constant.ExchangeStatus;
import com.yundao.bp.biz.constant.ExchangeType;
import com.yundao.bp.biz.entity.BizExchange;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 换房单视图。
 */
public record ExchangeVO(
        Long id,
        String exchangeNo,
        Long personId,
        Long oldContractId,
        Long oldHouseId,
        Long newHouseId,
        Long newContractId,
        String exchangeType,
        String exchangeTypeLabel,
        String exchangeReason,
        String exchangeStatus,
        String exchangeStatusLabel,
        Boolean grantMigrated,
        Integer exchangeTimes,
        Boolean forced,
        /** 是否已超成都"限换 1 次" */
        Boolean exchangeLimitReached,
        Boolean noExchangeFlag,
        BigDecimal rentMultiplier,
        Integer familySizeBefore,
        Integer familySizeAfter,
        String exchangeReasonCode,
        LocalDateTime createTime
) {
    public static ExchangeVO from(BizExchange e) {
        if (e == null) {
            return null;
        }
        ExchangeType tp;
        try {
            tp = ExchangeType.valueOf(e.getExchangeType());
        } catch (IllegalArgumentException ex) {
            tp = ExchangeType.VOLUNTARY;
        }
        ExchangeStatus st;
        try {
            st = ExchangeStatus.valueOf(e.getExchangeStatus());
        } catch (IllegalArgumentException ex) {
            st = ExchangeStatus.APPLYING;
        }
        int times = e.getExchangeTimes() == null ? 0 : e.getExchangeTimes();
        return new ExchangeVO(e.getId(), e.getExchangeNo(), e.getPersonId(),
                e.getOldContractId(), e.getOldHouseId(), e.getNewHouseId(),
                e.getNewContractId(), e.getExchangeType(), tp.label(), e.getExchangeReason(),
                e.getExchangeStatus(), st.label(),
                e.getGrantMigrated() != null && e.getGrantMigrated() == 1,
                times, e.getIsForced() != null && e.getIsForced() == 1,
                times >= 1,
                e.getNoExchangeFlag() != null && e.getNoExchangeFlag() == 1,
                e.getRentMultiplier(), e.getFamilySizeBefore(), e.getFamilySizeAfter(),
                e.getExchangeReasonCode(), e.getCreateTime());
    }
}
'''

count = 0
for rel, content in FILES.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个文件' % count)
