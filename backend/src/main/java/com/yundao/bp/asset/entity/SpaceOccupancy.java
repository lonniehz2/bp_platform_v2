package com.yundao.bp.asset.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 房源占用记录。对应表 {@code bp_asset_space_occupancy}。
 *
 * <p>这是「谁在什么时间占了哪套房」的权威流水，房源状态
 * （{@code bp_asset_house.house_status}）只是它的当前视图。
 *
 * <p>生命周期：
 * <ol>
 *   <li>合同生效 → 新增一条 {@code ACTIVE}，房源置为 {@code OCCUPIED}</li>
 *   <li>合同续签 → 更新该条的 {@code end_date}</li>
 *   <li>合同终止/到期/作废 → 该条置为 {@code FINISHED} 并回填实际结束日</li>
 * </ol>
 *
 * <p>同一房源允许多条并行占用（合租/床位），因此「是否还占着」要看
 * 是否还存在 {@code ACTIVE} 记录，不能只看房源状态。
 */
@TableName("bp_asset_space_occupancy")
public class SpaceOccupancy {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private Long spaceId;
    private Long houseId;
    private Long personId;
    /** 占用类型：CONTRACT 合同 / ALLOCATION 配租 / TEMP 临时 */
    private String occupyType;
    /** 是否主承租人：1 是 0 否（合租时区分主次） */
    private Integer isPrimary;
    private LocalDate startDate;
    private LocalDate endDate;
    /** ACTIVE 占用中 / FINISHED 已结束 */
    private String status;
    /** 来源单据类型：CONTRACT / ALLOCATION */
    private String sourceType;
    private Long sourceId;

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
    public Long getSpaceId() { return spaceId; }
    public void setSpaceId(Long spaceId) { this.spaceId = spaceId; }
    public Long getHouseId() { return houseId; }
    public void setHouseId(Long houseId) { this.houseId = houseId; }
    public Long getPersonId() { return personId; }
    public void setPersonId(Long personId) { this.personId = personId; }
    public String getOccupyType() { return occupyType; }
    public void setOccupyType(String occupyType) { this.occupyType = occupyType; }
    public Integer getIsPrimary() { return isPrimary; }
    public void setIsPrimary(Integer isPrimary) { this.isPrimary = isPrimary; }
    public LocalDate getStartDate() { return startDate; }
    public void setStartDate(LocalDate startDate) { this.startDate = startDate; }
    public LocalDate getEndDate() { return endDate; }
    public void setEndDate(LocalDate endDate) { this.endDate = endDate; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public String getSourceType() { return sourceType; }
    public void setSourceType(String sourceType) { this.sourceType = sourceType; }
    public Long getSourceId() { return sourceId; }
    public void setSourceId(Long sourceId) { this.sourceId = sourceId; }
    public String getCreateBy() { return createBy; }
    public void setCreateBy(String createBy) { this.createBy = createBy; }
    public LocalDateTime getCreateTime() { return createTime; }
    public void setCreateTime(LocalDateTime createTime) { this.createTime = createTime; }
    public String getUpdateBy() { return updateBy; }
    public void setUpdateBy(String updateBy) { this.updateBy = updateBy; }
    public LocalDateTime getUpdateTime() { return updateTime; }
    public void setUpdateTime(LocalDateTime updateTime) { this.updateTime = updateTime; }
}
