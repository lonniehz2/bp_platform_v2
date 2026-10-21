package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/**
 * 登记一次催缴。
 */
public record DunningCreateCmd(

        @NotNull(message = "账单不能为空")
        Long billId,

        Long personId,

        @NotBlank(message = "催缴方式不能为空")
        @Pattern(regexp = "SMS|WECHAT|PHONE|VISIT|NOTICE|PLATFORM", message = "催缴方式不合法")
        String dunningType,

        @Size(max = 1000, message = "催缴内容不能超过 1000 字")
        String dunningContent,

        String dunningResult,

        /** 佐证 URL（上门照片/通话记录）；上门、电话建议必填 */
        String evidenceUrl,

        Long operatorId
) {
}
