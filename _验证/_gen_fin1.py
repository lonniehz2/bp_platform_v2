# -*- coding: utf-8 -*-
"""生成 fin 资金账务（第 1 部分：常量/实体/Mapper/DTO）"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['fin/constant/BillStatus.java'] = '''package com.yundao.bp.fin.constant;

import java.util.Set;

/**
 * 账单状态（对应 {@code bp_fin_bill.bill_status}）。
 *
 * <pre>
 *   UNPAID 未缴 ──部分收款──> PARTIAL 部分缴 ──收满──> PAID 已缴
 *      │                        │
 *      └──过缴费截止日──> OVERDUE 已逾期（仍可收）
 *   UNPAID/PARTIAL/OVERDUE ──减免──> WAIVED 已免除
 *   任意未缴 ──作废──> CANCELLED（终态）
 * </pre>
 */
public enum BillStatus {

    UNPAID("未缴", false),
    PARTIAL("部分缴", false),
    PAID("已缴", true),
    OVERDUE("已逾期", false),
    WAIVED("已免除", true),
    CANCELLED("已作废", true);

    private final String label;
    private final boolean terminal;

    BillStatus(String label, boolean terminal) {
        this.label = label;
        this.terminal = terminal;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return terminal;
    }

    /** 是否还欠钱（可收款）。 */
    public boolean isOutstanding() {
        return this == UNPAID || this == PARTIAL || this == OVERDUE;
    }

    public static Set<BillStatus> nextOf(BillStatus from) {
        return switch (from) {
            case UNPAID -> Set.of(PARTIAL, PAID, OVERDUE, WAIVED, CANCELLED);
            case PARTIAL -> Set.of(PARTIAL, PAID, OVERDUE, WAIVED, CANCELLED);
            case OVERDUE -> Set.of(PARTIAL, PAID, WAIVED, CANCELLED);
            case PAID, WAIVED, CANCELLED -> Set.of();
        };
    }
}
'''

FILES['fin/constant/PayStatus.java'] = '''package com.yundao.bp.fin.constant;

/**
 * 收款单状态（对应 {@code bp_fin_payment.pay_status}）。
 *
 * <p>只有 {@code SUCCESS} 的收款单才能用于核销账单。
 */
public enum PayStatus {

    PENDING("待支付"),
    SUCCESS("成功"),
    FAILED("失败"),
    REFUNDED("已退款");

    private final String label;

    PayStatus(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    public boolean isSuccess() {
        return this == SUCCESS;
    }
}
'''

FILES['fin/entity/FinBill.java'] = '''package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 账单。对应 {@code bp_fin_bill}。
 */
@Data
@TableName("bp_fin_bill")
public class FinBill {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String billNo;
    private Long accountSetId;

    private Long orgId;
    private Long contractId;
    private Long houseId;
    private Long spaceId;

    private Long personId;
    private String payerName;
    private String payerPhone;

    private Long feeItemId;
    /** 账期，如 2026-10 */
    private String billPeriod;
    private LocalDate periodStart;
    private LocalDate periodEnd;

    private BigDecimal billAmount;
    private BigDecimal discountAmount;
    private BigDecimal lateFee;
    private BigDecimal paidAmount;
    private BigDecimal waivedAmount;
    /** 应付金额 = 应收 - 减免 + 滞纳金 - 已收 - 已免 */
    private BigDecimal payableAmount;

    private LocalDate dueDate;
    /** UNPAID / PARTIAL / PAID / OVERDUE / WAIVED / CANCELLED */
    private String billStatus;
    private Integer overdueDays;
    /** AUTO / MANUAL / IMPORT */
    private String generateType;
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
'''

FILES['fin/entity/FinPayment.java'] = '''package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 收款单。对应 {@code bp_fin_payment}。
 */
@Data
@TableName("bp_fin_payment")
public class FinPayment {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String paymentNo;
    private Long accountSetId;

    private Long orgId;
    private Long personId;
    private String payerName;

    private BigDecimal payAmount;
    /** WECHAT / ALIPAY / BANK / BANK_TRANSFER / CASH / POS / SELF_TERMINAL / OTHER */
    private String payChannel;
    private LocalDateTime payTime;
    private String tradeNo;

    /** PENDING / SUCCESS / FAILED / REFUNDED */
    private String payStatus;
    /** UNRECONCILED / RECONCILED / PARTIAL */
    private String reconcileStatus;
    private BigDecimal reconciledAmount;
    private Integer unknownFlag;

    private Long operatorId;
    private String remark;

    @TableField(fill = FieldFill.INSERT)
    private String createBy;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private String updateBy;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
'''

FILES['fin/entity/FinPaymentAllocate.java'] = '''package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 收款核销明细。对应 {@code bp_fin_payment_allocate}。
 *
 * <p>一条收款单可核销多张账单（如一次交清 3 个月租金），
 * 每次核销留一行痕迹，便于对账与冲销。
 */
@Data
@TableName("bp_fin_payment_allocate")
public class FinPaymentAllocate {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private Long paymentId;
    private Long billId;
    private BigDecimal allocateAmount;
    /** PAY 缴费核销 / REFUND 退款冲销 */
    private String allocateType;

    private String createBy;
    private LocalDateTime createTime;
}
'''

for mapper, entity in (('FinBillMapper', 'FinBill'),
                       ('FinPaymentMapper', 'FinPayment'),
                       ('FinPaymentAllocateMapper', 'FinPaymentAllocate')):
    FILES['fin/mapper/%s.java' % mapper] = '''package com.yundao.bp.fin.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.fin.entity.%s;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface %s extends BaseMapper<%s> {
}
''' % (entity, mapper, entity)

FILES['fin/dto/BillCreateCmd.java'] = '''package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 生成账单。
 *
 * <p>应付金额由服务端计算：{@code payable = 应收 - 减免 + 滞纳金 - 已收 - 已免}。
 */
public record BillCreateCmd(

        @NotNull(message = "收费项目不能为空")
        Long feeItemId,

        @NotNull(message = "组织不能为空")
        Long orgId,

        Long contractId,
        Long houseId,
        Long spaceId,
        Long personId,
        String payerName,
        String payerPhone,

        String billPeriod,

        @NotNull(message = "费用起始日不能为空")
        LocalDate periodStart,
        @NotNull(message = "费用截止日不能为空")
        LocalDate periodEnd,

        @NotNull(message = "应收金额不能为空")
        @DecimalMin(value = "0", message = "应收金额不能为负")
        BigDecimal billAmount,

        @DecimalMin(value = "0", message = "减免金额不能为负")
        BigDecimal discountAmount,

        @DecimalMin(value = "0", message = "滞纳金不能为负")
        BigDecimal lateFee,

        LocalDate dueDate,

        @Pattern(regexp = "^$|AUTO|MANUAL|IMPORT", message = "生成方式不合法")
        String generateType,

        String remark
) {
}
'''

FILES['fin/dto/PaymentCreateCmd.java'] = '''package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import java.math.BigDecimal;

/**
 * 登记收款。
 */
public record PaymentCreateCmd(

        @NotNull(message = "组织不能为空")
        Long orgId,
        Long personId,
        String payerName,

        @NotNull(message = "收款金额不能为空")
        @DecimalMin(value = "0.01", message = "收款金额必须大于 0")
        BigDecimal payAmount,

        @NotBlank(message = "收款渠道不能为空")
        @Pattern(regexp = "WECHAT|ALIPAY|BANK|BANK_TRANSFER|CASH|POS|SELF_TERMINAL|OTHER",
                message = "收款渠道不合法")
        String payChannel,

        String tradeNo,
        Long operatorId,
        /** 是否未知款项（来源不明，先挂账待查证） */
        Integer unknownFlag,
        String remark
) {
}
'''

FILES['fin/dto/BillVO.java'] = '''package com.yundao.bp.fin.dto;

import com.yundao.bp.fin.constant.BillStatus;
import com.yundao.bp.fin.entity.FinBill;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;

/**
 * 账单视图（含逾期派生）。
 */
public record BillVO(
        Long id,
        String billNo,
        Long orgId,
        Long contractId,
        Long houseId,
        Long personId,
        String payerName,
        Long feeItemId,
        String billPeriod,
        LocalDate periodStart,
        LocalDate periodEnd,
        BigDecimal billAmount,
        BigDecimal discountAmount,
        BigDecimal lateFee,
        BigDecimal paidAmount,
        BigDecimal waivedAmount,
        BigDecimal payableAmount,
        LocalDate dueDate,
        String billStatus,
        String billStatusLabel,
        Integer overdueDays,
        /** 派生：是否逾期未缴（实时计算） */
        Boolean overdueNow,
        String generateType,
        String remark,
        LocalDateTime createTime
) {
    public static BillVO from(FinBill e) {
        if (e == null) {
            return null;
        }
        BillStatus st;
        try {
            st = BillStatus.valueOf(e.getBillStatus());
        } catch (IllegalArgumentException ex) {
            st = BillStatus.UNPAID;
        }
        boolean overdueNow = false;
        long days = 0;
        if (st.isOutstanding() && e.getDueDate() != null
                && LocalDate.now().isAfter(e.getDueDate())) {
            overdueNow = true;
            days = ChronoUnit.DAYS.between(e.getDueDate(), LocalDate.now());
        }
        return new BillVO(e.getId(), e.getBillNo(), e.getOrgId(), e.getContractId(),
                e.getHouseId(), e.getPersonId(), e.getPayerName(), e.getFeeItemId(),
                e.getBillPeriod(), e.getPeriodStart(), e.getPeriodEnd(), e.getBillAmount(),
                e.getDiscountAmount(), e.getLateFee(), e.getPaidAmount(), e.getWaivedAmount(),
                e.getPayableAmount(), e.getDueDate(), e.getBillStatus(), st.label(),
                e.getOverdueDays(), overdueNow, e.getGenerateType(), e.getRemark(),
                e.getCreateTime());
    }
}
'''

FILES['fin/dto/PaymentVO.java'] = '''package com.yundao.bp.fin.dto;

import com.yundao.bp.fin.constant.PayStatus;
import com.yundao.bp.fin.entity.FinPayment;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 收款单视图（含"可核销余额"派生）。
 */
public record PaymentVO(
        Long id,
        String paymentNo,
        Long orgId,
        Long personId,
        String payerName,
        BigDecimal payAmount,
        String payChannel,
        LocalDateTime payTime,
        String tradeNo,
        String payStatus,
        String payStatusLabel,
        String reconcileStatus,
        BigDecimal reconciledAmount,
        /** 派生：可核销余额 = 收款金额 - 已核销 */
        BigDecimal remainAmount,
        Boolean unknownFlag,
        String remark,
        LocalDateTime createTime
) {
    public static PaymentVO from(FinPayment e) {
        if (e == null) {
            return null;
        }
        PayStatus st;
        try {
            st = PayStatus.valueOf(e.getPayStatus());
        } catch (IllegalArgumentException ex) {
            st = PayStatus.PENDING;
        }
        BigDecimal paid = e.getPayAmount() == null ? BigDecimal.ZERO : e.getPayAmount();
        BigDecimal done = e.getReconciledAmount() == null ? BigDecimal.ZERO : e.getReconciledAmount();
        return new PaymentVO(e.getId(), e.getPaymentNo(), e.getOrgId(), e.getPersonId(),
                e.getPayerName(), e.getPayAmount(), e.getPayChannel(), e.getPayTime(),
                e.getTradeNo(), e.getPayStatus(), st.label(), e.getReconcileStatus(),
                e.getReconciledAmount(), paid.subtract(done), 
                e.getUnknownFlag() != null && e.getUnknownFlag() == 1,
                e.getRemark(), e.getCreateTime());
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
