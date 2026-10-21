package com.yundao.bp.asset.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import java.math.BigDecimal;

/**
 * 创建房源。
 *
 * <p><b>关键约束</b>：
 * <ul>
 *   <li>{@code spaceId} 必须是 <b>ROOM 或 BED</b> 类型的空间节点
 *       （{@code SpaceType.canHostHouse()}），否则拒绝 —— 防止把房源挂到楼栋/单元上</li>
 *   <li>{@code orgId} <b>不由前端传入</b>，从 {@code spaceId} 对应的空间节点派生，
 *       避免跨组织挂载</li>
 *   <li>{@code houseCode} 在同一组织内唯一</li>
 *   <li>初始状态固定为 {@code PENDING_ALLOC}（待分配），已入住人数 0</li>
 * </ul>
 *
 * <p>枚举取值（与 DDL 注释一致）：
 * <pre>
 * houseType      PUBLIC_RENTAL 公租房 / AFFORDABLE_RENTAL 保租房 / TALENT 人才公寓 /
 *                APARTMENT 公寓 / DORMITORY 宿舍 / RENTAL 出租房 / HOTEL 酒店民宿
 * structType     VILLA / MULTI / SMALL_HIGH / HIGH / SUPER_HIGH
 * useType        CIVIL 民用 / COMMERCIAL 商用
 * decoration     ROUGH 毛坯 / SIMPLE 简装 / FINE 精装
 * securityType   LOW_RENT 廉租 / PUBLIC 公租 / AFFORDABLE 保租 / TALENT 人才
 * rentUnit       AREA_MONTH 元/㎡·月 / HOUSE_MONTH 元/套·月 / BED_MONTH 元/床·月 / HOUSE_NIGHT 元/套·夜
 * manageNature   SELF 自营 / ENTRUST 委托 / LEASE 租赁
 * propertyNature STATE 国有 / COLLECTIVE 集体 / PRIVATE 私有
 * </pre>
 */
public record HouseCreateCmd(

        @NotNull(message = "关联空间节点不能为空")
        Long spaceId,

        @NotBlank(message = "房源编号不能为空")
        @Size(max = 64, message = "房源编号不能超过 64 字符")
        String houseCode,

        @NotBlank(message = "房源名称不能为空")
        @Size(max = 128, message = "房源名称不能超过 128 字符")
        String houseName,

        @NotBlank(message = "房源类型不能为空")
        @Pattern(regexp = "PUBLIC_RENTAL|AFFORDABLE_RENTAL|TALENT|APARTMENT|DORMITORY|RENTAL|HOTEL",
                message = "房源类型不合法")
        String houseType,

        @Pattern(regexp = "^$|VILLA|MULTI|SMALL_HIGH|HIGH|SUPER_HIGH", message = "建筑类型不合法")
        String structType,

        @Pattern(regexp = "^$|CIVIL|COMMERCIAL", message = "用途不合法")
        String useType,

        @Size(max = 30, message = "户型不能超过 30 字符")
        String unitLayout,

        Integer floorNo,

        @Size(max = 20, message = "朝向不能超过 20 字符")
        String orientation,

        @DecimalMin(value = "0.01", message = "建筑面积必须大于 0")
        BigDecimal area,

        @DecimalMin(value = "0.01", message = "套内面积必须大于 0")
        BigDecimal innerArea,

        @Pattern(regexp = "^$|ROUGH|SIMPLE|FINE", message = "装修标准不合法")
        String decoration,

        @Pattern(regexp = "^$|LOW_RENT|PUBLIC|AFFORDABLE|TALENT", message = "保障类别不合法")
        String securityType,

        @DecimalMin(value = "0", message = "租金标准不能为负")
        BigDecimal rentStandard,

        @Pattern(regexp = "^$|AREA_MONTH|HOUSE_MONTH|BED_MONTH|HOUSE_NIGHT|BED_NIGHT", message = "租金计价单位不合法")
        String rentUnit,

        @Min(value = 1, message = "最大入住人数至少为 1")
        Integer maxCapacity,

        @Pattern(regexp = "^$|SELF|ENTRUST|LEASE", message = "经营性质不合法")
        String manageNature,

        @Pattern(regexp = "^$|STATE|COLLECTIVE|PRIVATE", message = "产权性质不合法")
        String propertyNature,

        Long ownerOrgId,
        Long adminOrgId,

        @Size(max = 64, message = "房源别名不能超过 64 字符")
        String houseAlias,

        @Size(max = 500, message = "备注不能超过 500 字符")
        String remark
) {
}
