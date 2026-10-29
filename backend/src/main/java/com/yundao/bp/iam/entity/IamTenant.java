package com.yundao.bp.iam.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;

/**
 * 租户。对应表 {@code bp_iam_tenant}。
 *
 * <p>⚠️ 本表<b>没有 tenant_id 列</b>（它本身就是租户主表），
 * 已在 {@code MybatisTenantConfig.IGNORE_TABLES} 中排除租户插件。
 */
@TableName("bp_iam_tenant")
public class IamTenant {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantCode;
    private String tenantName;
    /** GOV 政府 / ORG 运营机构 / ENTERPRISE 企业 */
    private String tenantType;
    private String regionCode;
    private String contactName;
    private String contactPhone;
    private String businessTypeCode;
    private Integer deleted;
    private LocalDateTime archiveTime;
    /** ROW 行级 / SCHEMA 独立Schema / DATABASE 独立库（一期只用 ROW） */
    private String isolationMode;
    /** ENABLED / DISABLED */
    private String status;

    private String createBy;
    private LocalDateTime createTime;
    private String updateBy;
    private LocalDateTime updateTime;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getTenantCode() { return tenantCode; }
    public void setTenantCode(String tenantCode) { this.tenantCode = tenantCode; }

    public String getTenantName() { return tenantName; }
    public void setTenantName(String tenantName) { this.tenantName = tenantName; }

    public String getTenantType() { return tenantType; }
    public void setTenantType(String tenantType) { this.tenantType = tenantType; }

    public String getRegionCode() { return regionCode; }
    public void setRegionCode(String regionCode) { this.regionCode = regionCode; }

    public String getIsolationMode() { return isolationMode; }
    public void setIsolationMode(String isolationMode) { this.isolationMode = isolationMode; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public String getCreateBy() { return createBy; }
    public void setCreateBy(String createBy) { this.createBy = createBy; }

    public LocalDateTime getCreateTime() { return createTime; }
    public void setCreateTime(LocalDateTime createTime) { this.createTime = createTime; }

    public String getUpdateBy() { return updateBy; }
    public void setUpdateBy(String updateBy) { this.updateBy = updateBy; }

    public LocalDateTime getUpdateTime() { return updateTime; }
    public void setUpdateTime(LocalDateTime updateTime) { this.updateTime = updateTime; }

    public String getContactName() { return contactName; }

    public void setContactName(String contactName) { this.contactName = contactName; }

    public String getContactPhone() { return contactPhone; }

    public void setContactPhone(String contactPhone) { this.contactPhone = contactPhone; }

    public String getBusinessTypeCode() { return businessTypeCode; }

    public void setBusinessTypeCode(String businessTypeCode) {
        this.businessTypeCode = businessTypeCode;
    }

    public Integer getDeleted() { return deleted; }

    public void setDeleted(Integer deleted) { this.deleted = deleted; }

    public LocalDateTime getArchiveTime() { return archiveTime; }

    public void setArchiveTime(LocalDateTime archiveTime) { this.archiveTime = archiveTime; }
}
