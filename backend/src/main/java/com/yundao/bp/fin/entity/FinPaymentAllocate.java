package com.yundao.bp.fin.entity;

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
