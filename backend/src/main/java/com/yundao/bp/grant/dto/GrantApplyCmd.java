package com.yundao.bp.grant.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import java.time.LocalDateTime;
import java.util.List;

/**
 * 授权申请。
 *
 * @param personId   被授权人员
 * @param spaceId    权限锚点空间（房源/房间节点）
 * @param grantLevel OWNERSHIP / MANAGEMENT / USAGE / VISIT
 * @param validStart 生效时间（为空=立即）
 * @param validEnd   失效时间（为空=永久，仅 OWNERSHIP 允许）
 * @param keyringIds 使用的钥匙包 ID 列表（为空=仅下发 App 权限）
 * @param sourceType 来源：CONTRACT / MANUAL / DELEGATE
 * @param sourceId   来源单据 ID
 * @param remark     备注
 */
public record GrantApplyCmd(

        @NotNull(message = "人员不能为空")
        Long personId,

        @NotNull(message = "授权空间不能为空")
        Long spaceId,

        @NotBlank(message = "权限层级不能为空")
        @Pattern(regexp = "OWNERSHIP|MANAGEMENT|USAGE|VISIT", message = "权限层级不合法")
        String grantLevel,

        LocalDateTime validStart,
        LocalDateTime validEnd,

        List<Long> keyringIds,

        @Pattern(regexp = "^$|CONTRACT|MANUAL|DELEGATE|TRANSFER", message = "来源类型不合法")
        String sourceType,

        Long sourceId,
        String remark
) {
}
