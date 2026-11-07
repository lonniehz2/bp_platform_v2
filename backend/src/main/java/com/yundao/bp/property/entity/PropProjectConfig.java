package com.yundao.bp.property.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/** 物业项目配置。项目组织本身仍使用 bp_iam_org。 */
@Data
@TableName("prop_project_config")
public class PropProjectConfig {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private Long orgId;
    private String projectCode;
    private String projectName;
    private String companyName;
    private String contactName;
    private String contactPhone;
    private String servicePhone;
    private String address;
    private String receiptHeader;
    private String bankAccount;
    private String status;

    @TableLogic
    private Integer isDeleted;
    private String createBy;
    private LocalDateTime createTime;
    private String updateBy;
    private LocalDateTime updateTime;
}
