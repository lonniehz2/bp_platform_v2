package com.yundao.bp.asset.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import java.math.BigDecimal;

/**
 * 创建空间节点。
 *
 * @param orgId       所属组织（小区）
 * @param parentId    父节点ID（为空表示顶级的楼栋/片区）
 * @param spaceCode   空间编码（租户内唯一）
 * @param spaceName   空间名称
 * @param spaceType   类型，见 SpaceType
 * @param area        面积（㎡）
 * @param sortNo      同级排序号（用于生成 path_code 段）
 * @param locationCode 五级地址编码（可空）
 */
public record SpaceCreateCmd(
        @NotNull(message = "所属组织不能为空") Long orgId,
        Long parentId,

        @NotBlank(message = "空间编码不能为空")
        @Size(max = 64, message = "空间编码不能超过 64 字符")
        String spaceCode,

        @NotBlank(message = "空间名称不能为空")
        @Size(max = 128, message = "空间名称不能超过 128 字符")
        String spaceName,

        @NotBlank(message = "空间类型不能为空")
        @Pattern(regexp = "AREA|BUILDING|UNIT|FLOOR|ROOM|BED|PARKING|GARAGE|SITE",
                message = "空间类型不合法")
        String spaceType,

        BigDecimal area,
        Integer sortNo,

        @Size(max = 64, message = "地址编码不能超过 64 字符")
        String locationCode
) {
}
