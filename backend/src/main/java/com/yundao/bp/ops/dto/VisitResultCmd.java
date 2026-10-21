package com.yundao.bp.ops.dto;

import jakarta.validation.constraints.Pattern;
import java.time.LocalDate;

/**
 * 回填走访结果。
 *
 * @param visitStatus     DONE / REFUSED / ABSENT / CANCELLED
 * @param actualDate      实际走访日期
 * @param isOccupied      是否实际有人居住
 * @param actualResidents 实际居住人数
 * @param matchResult     MATCH / MISMATCH / UNKNOWN
 * @param findings        发现情况
 * @param isSublease      是否发现转租转借
 * @param isIdle          是否发现闲置
 * @param isIllegalUse    是否发现违规使用
 * @param images          现场照片
 * @param location        签到定位
 * @param nextAction      后续处置建议
 */
public record VisitResultCmd(

        @Pattern(regexp = "DONE|REFUSED|ABSENT|CANCELLED", message = "走访状态不合法")
        String visitStatus,

        LocalDate actualDate,
        Integer isOccupied,
        Integer actualResidents,

        @Pattern(regexp = "^$|MATCH|MISMATCH|UNKNOWN", message = "匹配结果不合法")
        String matchResult,

        String findings,
        Integer isSublease,
        Integer isIdle,
        Integer isIllegalUse,
        String images,
        String location,
        String nextAction
) {
}
