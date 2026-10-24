package com.yundao.bp.asset.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 房源（配租实体）。对应表 {@code bp_asset_house}。
 *
 * <p>⭐ 房源挂在 {@code ROOM}（或 {@code BED}）节点上：
 * <b>空间是物理位置，房源是配租实体</b>。同一房间可拆分为多套可配租房源（合租/床位出租）。
 */
@TableName("bp_asset_house")
public class AssetHouse {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private Long orgId;
    /** 关联空间节点（应为 ROOM 或 BED） */
    private Long spaceId;
    private String houseCode;
    private String houseName;
    /** PUBLIC_RENTAL 公租房 / AFFORDABLE 保租房 / TALENT 人才公寓 / APARTMENT 公寓 / DORM 宿舍 / HOTEL 酒店民宿 / RENTAL 出租房 */
    private String houseType;
    private String structType;
    private String useType;
    private String unitLayout;
    private Integer floorNo;
    private String orientation;
    private BigDecimal area;
    private BigDecimal innerArea;
    private String decoration;
    /** 保障类型：PUBLIC / AFFORDABLE / TALENT / LOW_RENT */
    private String securityType;
    private BigDecimal rentStandard;
    private String rentUnit;
    private Integer maxCapacity;
    /** 计量模式：INDEPENDENT 独立表 / SHARED 分摊 / MIXED 独立+公区分摊 */
    private String meterMode;

    private Integer currentCapacity;
    /** 见 {@code HouseStatus} */
    private String houseStatus;
    private String useStatus;
    private String manageNature;
    private String propertyNature;
    private Long ownerOrgId;
    private Long adminOrgId;
    /** 户主（自然人，政策确认；与 owner_org_id 并存） */
    private Long ownerPersonId;
    private String houseAlias;
    private String thirdRoomNo;
    private LocalDateTime lockStatusTime;
    private String remark;

    @TableLogic
    private Integer isDeleted;

    @TableField(fill = FieldFill.INSERT)
    private String createBy;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private String updateBy;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getTenantId() { return tenantId; }
    public void setTenantId(String tenantId) { this.tenantId = tenantId; }
    public Long getOrgId() { return orgId; }
    public void setOrgId(Long orgId) { this.orgId = orgId; }
    public Long getSpaceId() { return spaceId; }
    public void setSpaceId(Long spaceId) { this.spaceId = spaceId; }
    public String getHouseCode() { return houseCode; }
    public void setHouseCode(String houseCode) { this.houseCode = houseCode; }
    public String getHouseName() { return houseName; }
    public void setHouseName(String houseName) { this.houseName = houseName; }
    public String getHouseType() { return houseType; }
    public void setHouseType(String houseType) { this.houseType = houseType; }
    public String getStructType() { return structType; }
    public void setStructType(String structType) { this.structType = structType; }
    public String getUseType() { return useType; }
    public void setUseType(String useType) { this.useType = useType; }
    public String getUnitLayout() { return unitLayout; }
    public void setUnitLayout(String unitLayout) { this.unitLayout = unitLayout; }
    public Integer getFloorNo() { return floorNo; }
    public void setFloorNo(Integer floorNo) { this.floorNo = floorNo; }
    public String getOrientation() { return orientation; }
    public void setOrientation(String orientation) { this.orientation = orientation; }
    public BigDecimal getArea() { return area; }
    public void setArea(BigDecimal area) { this.area = area; }
    public BigDecimal getInnerArea() { return innerArea; }
    public void setInnerArea(BigDecimal innerArea) { this.innerArea = innerArea; }
    public String getDecoration() { return decoration; }
    public void setDecoration(String decoration) { this.decoration = decoration; }
    public String getSecurityType() { return securityType; }
    public void setSecurityType(String securityType) { this.securityType = securityType; }
    public BigDecimal getRentStandard() { return rentStandard; }
    public void setRentStandard(BigDecimal rentStandard) { this.rentStandard = rentStandard; }
    public String getRentUnit() { return rentUnit; }
    public void setRentUnit(String rentUnit) { this.rentUnit = rentUnit; }
    public Integer getMaxCapacity() { return maxCapacity; }
    public void setMaxCapacity(Integer maxCapacity) { this.maxCapacity = maxCapacity; }
    public Integer getCurrentCapacity() { return currentCapacity; }
    public void setCurrentCapacity(Integer currentCapacity) { this.currentCapacity = currentCapacity; }
    public String getHouseStatus() { return houseStatus; }
    public void setHouseStatus(String houseStatus) { this.houseStatus = houseStatus; }
    public String getUseStatus() { return useStatus; }
    public void setUseStatus(String useStatus) { this.useStatus = useStatus; }
    public String getManageNature() { return manageNature; }
    public void setManageNature(String manageNature) { this.manageNature = manageNature; }
    public String getPropertyNature() { return propertyNature; }
    public void setPropertyNature(String propertyNature) { this.propertyNature = propertyNature; }
    public Long getOwnerOrgId() { return ownerOrgId; }
    public void setOwnerOrgId(Long ownerOrgId) { this.ownerOrgId = ownerOrgId; }
    public Long getAdminOrgId() { return adminOrgId; }
    public void setAdminOrgId(Long adminOrgId) { this.adminOrgId = adminOrgId; }
    public Long getOwnerPersonId() { return ownerPersonId; }
    public void setOwnerPersonId(Long ownerPersonId) { this.ownerPersonId = ownerPersonId; }
    public String getHouseAlias() { return houseAlias; }
    public void setHouseAlias(String houseAlias) { this.houseAlias = houseAlias; }
    public String getThirdRoomNo() { return thirdRoomNo; }
    public void setThirdRoomNo(String thirdRoomNo) { this.thirdRoomNo = thirdRoomNo; }
    public LocalDateTime getLockStatusTime() { return lockStatusTime; }
    public void setLockStatusTime(LocalDateTime lockStatusTime) { this.lockStatusTime = lockStatusTime; }
    public String getRemark() { return remark; }
    public void setRemark(String remark) { this.remark = remark; }
    public Integer getIsDeleted() { return isDeleted; }
    public void setIsDeleted(Integer isDeleted) { this.isDeleted = isDeleted; }
    public String getCreateBy() { return createBy; }
    public void setCreateBy(String createBy) { this.createBy = createBy; }
    public LocalDateTime getCreateTime() { return createTime; }
    public void setCreateTime(LocalDateTime createTime) { this.createTime = createTime; }
    public String getUpdateBy() { return updateBy; }
    public void setUpdateBy(String updateBy) { this.updateBy = updateBy; }
    public LocalDateTime getUpdateTime() { return updateTime; }
    public void setUpdateTime(LocalDateTime updateTime) { this.updateTime = updateTime; }

    public String getMeterMode() { return meterMode; }
    public void setMeterMode(String meterMode) { this.meterMode = meterMode; }
}
