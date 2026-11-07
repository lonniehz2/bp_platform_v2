package com.yundao.bp.property.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/** 物业收入/支出分类。系统分类不可删除，租户只能扩展叶子分类。 */
@Data
@TableName("prop_category")
public class PropCategory {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    /** INCOME / EXPENSE */
    private String categoryType;
    private Long parentId;
    private String categoryCode;
    private String categoryName;
    private Integer categoryLevel;
    private Integer isSystem;
    private Integer isLeaf;
    private Integer allowCustom;
    private String reportLineCode;
    /** ENABLED / DISABLED */
    private String status;
    private Integer sortNo;
    private String remark;

    @TableLogic
    private Integer isDeleted;
    private String createBy;
    private LocalDateTime createTime;
    private String updateBy;
    private LocalDateTime updateTime;
}
