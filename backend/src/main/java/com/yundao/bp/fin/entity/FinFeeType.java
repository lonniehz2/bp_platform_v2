package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 费用类型字典。对应 {@code bp_fin_fee_type}。
 *
 * <p>计费项目的「费用类型」从这里取值，可在界面增删改（停用而非物理删除）。
 */
@Data
@TableName("bp_fin_fee_type")
public class FinFeeType {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;

    /** 类型编码，如 RENT */
    private String typeCode;

    /** 类型名称，如 租金 */
    private String typeName;

    /** ENABLED / DISABLED */
    private String status;

    private Integer sortNo;

    @TableLogic
    private Integer isDeleted;

    @TableField(fill = FieldFill.INSERT)
    private String createBy;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
