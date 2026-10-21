package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 催缴记录。对应 {@code bp_fin_dunning_record}。
 *
 * <p>同一账单可多次催缴，{@code dunning_no} 为第几次催缴（1、2、3…）。
 */
@Data
@TableName("bp_fin_dunning_record")
public class FinDunningRecord {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private Long billId;
    private Long personId;

    /** 第几次催缴 */
    private Integer dunningNo;
    /** SMS / WECHAT / PHONE / VISIT / NOTICE / PLATFORM */
    private String dunningType;
    private LocalDateTime dunningTime;
    private String dunningContent;
    private String dunningResult;
    /** 佐证（上门照片/通话记录） */
    private String evidenceUrl;
    private Long operatorId;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
}
