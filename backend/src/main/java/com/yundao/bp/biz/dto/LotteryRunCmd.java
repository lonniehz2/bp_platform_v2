package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.NotNull;

/**
 * 执行摇号。
 *
 * @param seed 随机种子；为空则由系统生成并落库（公证留痕、结果可复现）
 */
public record LotteryRunCmd(

        /** 批次 ID：兼容前端传数字/字符串/对象（{id:...}）三种形式 */
        @NotNull(message = "批次不能为空")
        Object batchId,

        String seed,

        /** 公证信息（公证处/公证员/公证书号） */
        String notaryInfo
) {
}
