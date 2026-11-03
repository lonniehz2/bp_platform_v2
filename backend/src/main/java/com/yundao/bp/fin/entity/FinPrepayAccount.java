package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import lombok.Data;

/** 合同预收余额账户。 */
@Data
@TableName("bp_fin_prepay_account")
public class FinPrepayAccount {
    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private Long contractId;
    private Long personId;
    private Long orgId;
    private BigDecimal balanceAmount;
    private BigDecimal totalIn;
    private BigDecimal totalOut;
    private String status;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
