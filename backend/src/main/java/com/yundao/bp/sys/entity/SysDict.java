package com.yundao.bp.sys.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 数据字典。对应 `bp_sys_dict`。
 *
 * <p>租户级可覆盖系统内置：{@code tenant_id} 为空表示系统内置。
 */
@Data
@TableName("bp_sys_dict")
public class SysDict {

    @TableId(type = IdType.INPUT)
    private Long id;

    /** 租户ID（NULL 表示系统内置） */
    private String tenantId;
    private String dictType;
    private String dictCode;
    private String dictLabel;
    private String dictValue;
    private Integer sortNo;
    private String cssClass;
    private Integer isDefault;
    /** ENABLED / DISABLED */
    private String dictStatus;
    private String remark;

    @TableLogic
    private Integer isDeleted;

    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
