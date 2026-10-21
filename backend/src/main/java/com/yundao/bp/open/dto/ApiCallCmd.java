package com.yundao.bp.open.dto;

import jakarta.validation.constraints.NotBlank;

/**
 * 开放接口调用请求（由开放网关统一入口校验后转发）。
 */
public record ApiCallCmd(

        @NotBlank(message = "AppKey 不能为空")
        String appKey,

        /** 接口编码（与 bp_open_api.api_code 对应） */
        @NotBlank(message = "接口编码不能为空")
        String apiCode,

        /** 毫秒时间戳 */
        @NotBlank(message = "timestamp 不能为空")
        String timestamp,

        @NotBlank(message = "nonce 不能为空")
        String nonce,

        @NotBlank(message = "sign 不能为空")
        String sign,

        String body
) {
}
