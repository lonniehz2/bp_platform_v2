package com.yundao.bp.ops.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/**
 * 创建工单。
 */
public record WorkOrderCreateCmd(

        @NotBlank(message = "工单类型不能为空")
        @Pattern(regexp = "REPAIR|INSPECT|INSTALL|MAINTAIN|COMPLAINT|CONSULT|ALERT|VISIT",
                message = "工单类型不合法")
        String orderType,

        @Pattern(regexp = "^$|TENANT_APP|MINIAPP|STAFF|ALERT|PHONE|WALKIN|IMPORT",
                message = "来源不合法")
        String orderSource,

        @NotBlank(message = "工单标题不能为空")
        @Size(max = 255, message = "标题不能超过 255 字符")
        String orderTitle,

        @Size(max = 2000, message = "问题描述不能超过 2000 字符")
        String orderContent,

        Long orgId,
        Long spaceId,
        Long houseId,
        String deviceId,
        String deviceType,
        Long personId,
        String reporterName,
        String reporterPhone,
        String orderAddress,
        String images,

        /** 响应时限（分钟），为空按工单类型默认值 */
        Integer slaResponseMinutes,
        /** 完工时限（分钟），为空按工单类型默认值 */
        Integer slaFinishMinutes,
        String remark
) {
}
