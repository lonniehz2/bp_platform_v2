package com.yundao.bp.biz.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 合同同住人。对应 {@code bp_biz_contract_cohabitant}。
 *
 * <p>同住人是保障房的关键数据：<b>按人补贴</b>、<b>年审人口核查</b>、
 * <b>退租腾退</b>、<b>门禁授权</b>都依赖它。
 */
@Data
@TableName("bp_biz_contract_cohabitant")
public class BizContractCohabitant {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private Long contractId;
    private Long personId;

    private String memberName;
    /** 身份证脱敏（不存明文） */
    private String idCardMask;
    /** 与承租人关系 */
    private String relation;
    /** 是否已授权开门 */
    private Integer isGranted;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
}
