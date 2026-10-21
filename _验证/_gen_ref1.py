# -*- coding: utf-8 -*-
"""生成 fin 退款单 + 押金台账"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

# ==================== 常量 ====================
FILES['fin/constant/RefundStatus.java'] = '''package com.yundao.bp.fin.constant;

import java.util.Set;

/**
 * 退款单状态机（对应 {@code bp_fin_refund.refund_status}）。
 *
 * <pre>
 *   PENDING 待审批 ──批准──> APPROVED 已批准 ──打款──> SUCCESS 已退款（终态）
 *        │                      │
 *     驳回                    失败
 *        ↓                      ↓
 *   REJECTED（终态）        FAILED（可重试回 APPROVED）
 * </pre>
 */
public enum RefundStatus {

    PENDING("待审批", false),
    APPROVED("已批准", false),
    SUCCESS("已退款", true),
    FAILED("失败", false),
    REJECTED("已驳回", true);

    private final String label;
    private final boolean terminal;

    RefundStatus(String label, boolean terminal) {
        this.label = label;
        this.terminal = terminal;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return terminal;
    }

    public static Set<RefundStatus> nextOf(RefundStatus from) {
        return switch (from) {
            case PENDING -> Set.of(APPROVED, REJECTED);
            case APPROVED -> Set.of(SUCCESS, FAILED);
            case FAILED -> Set.of(APPROVED);
            case SUCCESS, REJECTED -> Set.of();
        };
    }
}
'''

FILES['fin/constant/DepositStatus.java'] = '''package com.yundao.bp.fin.constant;

/**
 * 押金台账状态（对应 {@code bp_fin_deposit.deposit_status}）。
 */
public enum DepositStatus {

    HELD("已收取"),
    PARTIAL_REFUND("部分退还"),
    REFUNDED("已退还"),
    DEDUCTED("已抵扣");

    private final String label;

    DepositStatus(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    public boolean isClosed() {
        return this == REFUNDED || this == DEDUCTED;
    }
}
'''

# ==================== 实体 ====================
FILES['fin/entity/FinRefund.java'] = '''package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 退款单。对应 {@code bp_fin_refund}。
 */
@Data
@TableName("bp_fin_refund")
public class FinRefund {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String refundNo;

    private Long paymentId;
    private Long personId;
    private Long contractId;

    private BigDecimal refundAmount;
    private String refundReason;
    /** DEPOSIT / OVERPAY / OTHER */
    private String refundType;
    /** ORIGINAL / BANK / CASH */
    private String refundChannel;
    /** PENDING / APPROVED / SUCCESS / FAILED / REJECTED */
    private String refundStatus;

    private Long approveById;
    private LocalDateTime approveTime;
    private LocalDateTime refundTime;

    @TableField(fill = FieldFill.INSERT)
    private String createBy;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
'''

FILES['fin/entity/FinDeposit.java'] = '''package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 押金台账。对应 {@code bp_fin_deposit}。
 *
 * <p>一台合同一条台账，贯穿"收押金 → 抵扣 → 退还"全过程。
 * 政策上限：成都规定押金不超过 1000 元，超限时 {@code over_cap_flag=1}。
 */
@Data
@TableName("bp_fin_deposit")
public class FinDeposit {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private Long contractId;
    private Long personId;

    /** 应收押金 */
    private BigDecimal depositAmount;
    /** 已收押金 */
    private BigDecimal paidAmount;
    /** 已抵扣金额（如损坏赔偿） */
    private BigDecimal deductAmount;
    /** 已退还金额 */
    private BigDecimal refundAmount;
    /** 押金余额 = 已收 - 已抵扣 - 已退还 */
    private BigDecimal balanceAmount;

    /** HELD / PARTIAL_REFUND / REFUNDED / DEDUCTED */
    private String depositStatus;

    /** 政策规定上限（成都 1000 元） */
    private BigDecimal capAmount;
    private Integer isExempt;
    private String exemptReason;
    private Integer overCapFlag;

    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
'''

for mapper, entity in (('FinRefundMapper', 'FinRefund'), ('FinDepositMapper', 'FinDeposit')):
    FILES['fin/mapper/%s.java' % mapper] = '''package com.yundao.bp.fin.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.fin.entity.%s;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface %s extends BaseMapper<%s> {
}
''' % (entity, mapper, entity)

# ==================== DTO ====================
FILES['fin/dto/DepositCreateCmd.java'] = '''package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;

/**
 * 建立押金台账（签约时调用）。
 *
 * <p>若 {@code capAmount} 非空且应收押金超过它，则自动标记 {@code overCapFlag=1}
 * 并在返回中提示（成都政策：押金不超过 1000 元）。
 */
public record DepositCreateCmd(

        @NotNull(message = "合同不能为空")
        Long contractId,

        @NotNull(message = "人员不能为空")
        Long personId,

        @NotNull(message = "应收押金不能为空")
        @DecimalMin(value = "0", message = "押金不能为负")
        BigDecimal depositAmount,

        /** 已收押金（为空则视为 0，后续可补收） */
        @DecimalMin(value = "0", message = "已收押金不能为负")
        BigDecimal paidAmount,

        /** 政策上限（成都 1000），为空则不校验 */
        BigDecimal capAmount,

        /** 是否免收（廉租标准免收） */
        Integer isExempt,
        String exemptReason
) {
}
'''

FILES['fin/dto/RefundCreateCmd.java'] = '''package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import java.math.BigDecimal;

/**
 * 申请退款。
 */
public record RefundCreateCmd(

        Long paymentId,
        Long personId,
        Long contractId,

        @NotNull(message = "退款金额不能为空")
        @DecimalMin(value = "0.01", message = "退款金额必须大于 0")
        BigDecimal refundAmount,

        @NotBlank(message = "退款类型不能为空")
        @Pattern(regexp = "DEPOSIT|OVERPAY|OTHER", message = "退款类型不合法")
        String refundType,

        @Pattern(regexp = "^$|ORIGINAL|BANK|CASH", message = "退款渠道不合法")
        String refundChannel,

        String refundReason
) {
}
'''

FILES['fin/dto/DepositVO.java'] = '''package com.yundao.bp.fin.dto;

import com.yundao.bp.fin.constant.DepositStatus;
import com.yundao.bp.fin.entity.FinDeposit;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 押金台账视图。
 */
public record DepositVO(
        Long id,
        Long contractId,
        Long personId,
        BigDecimal depositAmount,
        BigDecimal paidAmount,
        BigDecimal deductAmount,
        BigDecimal refundAmount,
        BigDecimal balanceAmount,
        String depositStatus,
        String depositStatusLabel,
        BigDecimal capAmount,
        Boolean exempt,
        String exemptReason,
        /** 是否超政策上限（成都 1000 元） */
        Boolean overCap,
        /** 派生：尚欠收押金 = 应收 - 已收 */
        BigDecimal unpaidAmount,
        LocalDateTime createTime
) {
    public static DepositVO from(FinDeposit e) {
        if (e == null) {
            return null;
        }
        DepositStatus st;
        try {
            st = DepositStatus.valueOf(e.getDepositStatus());
        } catch (IllegalArgumentException ex) {
            st = DepositStatus.HELD;
        }
        BigDecimal due = e.getDepositAmount() == null ? BigDecimal.ZERO : e.getDepositAmount();
        BigDecimal paid = e.getPaidAmount() == null ? BigDecimal.ZERO : e.getPaidAmount();
        return new DepositVO(e.getId(), e.getContractId(), e.getPersonId(), e.getDepositAmount(),
                e.getPaidAmount(), e.getDeductAmount(), e.getRefundAmount(), e.getBalanceAmount(),
                e.getDepositStatus(), st.label(), e.getCapAmount(),
                e.getIsExempt() != null && e.getIsExempt() == 1, e.getExemptReason(),
                e.getOverCapFlag() != null && e.getOverCapFlag() == 1,
                due.subtract(paid), e.getCreateTime());
    }
}
'''

FILES['fin/dto/RefundVO.java'] = '''package com.yundao.bp.fin.dto;

import com.yundao.bp.fin.constant.RefundStatus;
import com.yundao.bp.fin.entity.FinRefund;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 退款单视图。
 */
public record RefundVO(
        Long id,
        String refundNo,
        Long paymentId,
        Long personId,
        Long contractId,
        BigDecimal refundAmount,
        String refundReason,
        String refundType,
        String refundChannel,
        String refundStatus,
        String refundStatusLabel,
        Long approveById,
        LocalDateTime approveTime,
        LocalDateTime refundTime,
        LocalDateTime createTime
) {
    public static RefundVO from(FinRefund e) {
        if (e == null) {
            return null;
        }
        RefundStatus st;
        try {
            st = RefundStatus.valueOf(e.getRefundStatus());
        } catch (IllegalArgumentException ex) {
            st = RefundStatus.PENDING;
        }
        return new RefundVO(e.getId(), e.getRefundNo(), e.getPaymentId(), e.getPersonId(),
                e.getContractId(), e.getRefundAmount(), e.getRefundReason(), e.getRefundType(),
                e.getRefundChannel(), e.getRefundStatus(), st.label(), e.getApproveById(),
                e.getApproveTime(), e.getRefundTime(), e.getCreateTime());
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
