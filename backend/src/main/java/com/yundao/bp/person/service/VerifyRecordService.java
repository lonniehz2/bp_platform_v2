package com.yundao.bp.person.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.person.entity.PersonVerifyRecord;
import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

/**
 * 实名认证留痕服务。
 *
 * <p><b>为什么必须留痕</b>：实名认证是保障资格的入口，一旦出事（冒名申请）
 * 必须能追溯「谁在什么时候、通过什么渠道、用什么材料、结果如何」。
 * 因此本模块<b>只追加，不提供修改与删除</b>。
 *
 * <p>人脸比对结果按 IoT 规范有 6 种取值（1 同一人 / 2 不同人 / 3 不能确定 /
 * 4 无法比对 / 5 库中无照片 / 0 空），<b>不能只存「通过/不通过」</b>，
 * 否则无法区分「确认不是本人」与「照片糊了比对不了」。
 */
public interface VerifyRecordService {

    /** 记录一次认证（由认证调用方在拿到结果后写入）。 */
    PersonVerifyRecord record(Long personId, String verifyType, String userName,
                              String idCardHash, String faceImgUrl, String idcardImgUrl,
                              String commandId, String responseCode, String resultCode,
                              BigDecimal faceScore, String faceResult,
                              String citizenResult, String rawResponse);

    PersonVerifyRecord get(Long id);

    PageResult<PersonVerifyRecord> page(long pageNum, long pageSize, Long personId,
                                        String verifyType, Boolean passOnly, String keyword);

    /** ⭐ 某人的认证结论（用于申请校验时快速判断）。 */
    Map<String, Object> conclusion(Long personId);

    /** 失败原因分布（运维/风控看板）。 */
    Map<String, Object> failStats();
}
