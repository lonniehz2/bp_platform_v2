package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import lombok.Data;

/** 押金转移 */
@Data
@TableName("bp_fin_deposit_transfer")
public class DepositTransfer {
    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private Long exchangeId;
    private Long oldContractId;
    private Long newContractId;
    private Long oldDepositId;
    private Long newDepositId;
    private BigDecimal transferAmount;
    private Long operatorId;
    private LocalDateTime createTime;
}
