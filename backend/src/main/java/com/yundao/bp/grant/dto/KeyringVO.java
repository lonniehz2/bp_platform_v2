package com.yundao.bp.grant.dto;

import com.yundao.bp.grant.constant.KeyClass;
import com.yundao.bp.grant.constant.KeyType;
import com.yundao.bp.grant.entity.GrantKeyring;
import java.time.LocalDateTime;

/**
 * 钥匙视图（<b>不回显介质值</b>，避免人脸/指纹/密码泄露）。
 */
public record KeyringVO(
        Long id,
        Long personId,
        String keyType,
        String keyTypeLabel,
        String keyClass,
        String keyClassLabel,
        String keyAlias,
        String channelType,
        String keySource,
        String verifyWay,
        Boolean real,
        String syncScope,
        String keyStatus,
        LocalDateTime expireTime,
        LocalDateTime createTime
) {
    public static KeyringVO from(GrantKeyring e) {
        if (e == null) {
            return null;
        }
        KeyType t = KeyType.of(e.getKeyType());
        KeyClass c = KeyClass.of(e.getKeyClass());
        return new KeyringVO(e.getId(), e.getPersonId(), e.getKeyType(),
                t == null ? e.getKeyType() : t.label(), e.getKeyClass(),
                c == null ? e.getKeyClass() : c.label(), e.getKeyAlias(),
                e.getChannelType(), e.getKeySource(), e.getVerifyWay(),
                e.getIsReal() != null && e.getIsReal() == 1, e.getSyncScope(),
                e.getKeyStatus(), e.getExpireTime(), e.getCreateTime());
    }
}
