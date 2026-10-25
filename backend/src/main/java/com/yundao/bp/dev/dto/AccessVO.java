package com.yundao.bp.dev.dto;

import com.yundao.bp.dev.entity.DevAccessRecord;
import java.time.LocalDateTime;

/**
 * 开门记录视图。
 */
public record AccessVO(
        Long id,
        String eventId,
        String lockId,
        String lockIdName,
        Long houseId,
        Long spaceId,
        Long personId,
        String targetUserMobile,
        String openType,
        String openTypeName,
        Boolean trusted,
        LocalDateTime openTime,
        String source,
        Boolean abnormal,
        String abnormalType
) {
    public static AccessVO from(DevAccessRecord e) {
        if (e == null) {
            return null;
        }
        return new AccessVO(e.getId(), e.getEventId(), e.getLockId(), null, e.getHouseId(),
                e.getSpaceId(), e.getPersonId(), e.getTargetUserMobile(), e.getOpenType(),
                e.getOpenTypeName(), e.getIsTrusted() != null && e.getIsTrusted() == 1,
                e.getOpenTime(), e.getSource(),
                e.getIsAbnormal() != null && e.getIsAbnormal() == 1, e.getAbnormalType());
    }
}
