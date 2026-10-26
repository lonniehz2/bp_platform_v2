package com.yundao.bp.asset.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import java.math.BigDecimal;

/**
 * 空间节点更新：只允许改名称/编码/面积/排序/状态/备注。
 *
 * <p>层级关系（父节点、类型）不在此调整——移挂会破坏 path_code 与授权链，
 * 需要走专门的重挂流程。
 */
public record SpaceUpdateCmd(

        @NotBlank(message = "空间名称不能为空")
        String spaceName,

        @NotBlank(message = "空间编码不能为空")
        String spaceCode,

        @DecimalMin(value = "0", message = "面积不能为负")
        BigDecimal area,

        Integer sortNo,

        @Pattern(regexp = "^$|ENABLED|DISABLED", message = "状态不合法")
        String status,

        String remark
) {
}
